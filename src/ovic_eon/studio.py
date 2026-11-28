"""On-device camera and image viewer for the EON ERS SDK."""

from __future__ import annotations

import argparse
import asyncio
import io
import threading
import time
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Full, Queue
from uuid import uuid4

from PIL import Image, ImageDraw, ImageOps

from ovic_eon.ers import EmotionObservation, ERSClient, ERSConfig

BG = "#0c121b"
PANEL = "#151f2c"
TEXT = "#f2f6fb"
MUTED = "#a7b7ca"
ACCENT = "#66e4ca"


@dataclass(frozen=True)
class Frame:
    image: Image.Image | None = None
    observation: EmotionObservation | None = None
    message: str = ""


def load_image(path: Path, config: ERSConfig) -> Image.Image:
    with path.open("rb") as stream:
        data = stream.read(config.max_image_bytes + 1)
    if len(data) > config.max_image_bytes:
        raise ValueError("Image exceeds the SDK input size limit.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as image:
            if max(image.size) > config.max_image_dimension:
                raise ValueError(
                    f"Image exceeds {config.max_image_dimension} pixels on its longest side."
                )
            return ImageOps.exif_transpose(image).convert("RGB")


@contextmanager
def camera_frames(index: int) -> Iterator[Iterator[Image.Image]]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError('Install the SDK with the "studio" extra to use a camera.') from exc

    camera = cv2.VideoCapture(index)
    try:
        if not camera.isOpened():
            raise RuntimeError(f"Camera {index} is unavailable. Check your device and OS settings.")
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

        def frames() -> Iterator[Image.Image]:
            while True:
                ok, frame = camera.read()
                if not ok:
                    raise RuntimeError("The camera stopped delivering frames.")
                yield Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        yield frames()
    finally:
        camera.release()


async def analyze(
    client: ERSClient, session: str, reference: str, image: Image.Image
) -> EmotionObservation:
    payload = io.BytesIO()
    image.save(payload, format="JPEG", quality=90)
    result = await client.analyze_image(session, reference, payload.getvalue())
    if not isinstance(result, EmotionObservation):
        raise RuntimeError("Expected an observation from the local SDK.")
    return result


def overlay(image: Image.Image, observation: EmotionObservation) -> Image.Image:
    shown = image.copy()
    box = observation.face_bbox
    if box:
        width, height = shown.size
        coords = (
            round(box["x_min"] * (width - 1)),
            round(box["y_min"] * (height - 1)),
            round(box["x_max"] * (width - 1)),
            round(box["y_max"] * (height - 1)),
        )
        color = ACCENT if observation.is_validated else "#f9c478"
        ImageDraw.Draw(shown).rectangle(coords, outline=color, width=max(2, width // 160))
    return shown


def publish(results: Queue[Frame], frame: Frame) -> None:
    try:
        results.put_nowait(frame)
    except Full:
        try:
            results.get_nowait()
        except Empty:
            pass
        results.put_nowait(frame)


async def run_source(
    config: ERSConfig,
    source: Path | int,
    stop: threading.Event,
    results: Queue[Frame],
) -> None:
    # Starting capture or selecting an image is the local user's opt-in.
    session, reference = uuid4().hex, uuid4().hex
    async with ERSClient(config=config) as client:
        await client.register_consent(session, reference)
        try:
            if isinstance(source, Path):
                image = load_image(source, config)
                obs = await analyze(client, session, reference, image)
                publish(results, Frame(image, obs, f"Image / {source.name}"))
                return

            with camera_frames(source) as frames:
                for image in frames:
                    if stop.is_set():
                        break
                    started = time.monotonic()
                    image.thumbnail((config.max_image_dimension, config.max_image_dimension))
                    obs = await analyze(client, session, reference, image)
                    if stop.is_set():
                        break
                    publish(results, Frame(image, obs, f"Live / Camera {source}"))
                    stop.wait(max(0.0, 0.125 - (time.monotonic() - started)))
        finally:
            await client.revoke_consent(session)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EON ERS Studio. Runs directly on this device.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--facial-model", help="Path to an optional local facial ONNX model")
    args = parser.parse_args(argv)

    try:
        import tkinter as tk
        from tkinter import filedialog

        from PIL import ImageTk

        root = tk.Tk()
    except (ImportError, RuntimeError) as exc:
        parser.exit(1, f"ERS Studio requires Tkinter and a desktop display: {exc}\n")
    except tk.TclError as exc:
        parser.exit(1, f"ERS Studio could not open a desktop window: {exc}\n")

    config = ERSConfig(
        facial_model_path=args.facial_model,
        face_detector="opencv",
        enable_speech=False,
        enable_text=False,
        enable_video=False,
        enable_multimodal_fusion=False,
    )
    root.title("OVIC Labs | EON Observation Studio")
    root.geometry("1100x730")
    root.minsize(850, 600)
    root.configure(bg=BG)
    results: Queue[Frame] = Queue(maxsize=1)
    worker: threading.Thread | None = None
    stop = threading.Event()
    current = Frame(message="Ready")
    preview: ImageTk.PhotoImage | None = None

    def label(parent: tk.Misc, text: str, size: int, color: str = TEXT, bg: str = BG) -> tk.Label:
        return tk.Label(parent, text=text, fg=color, bg=bg, font=("Segoe UI", size), anchor="w")

    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=28, pady=(22, 16))
    label(header, "EON   /   Observation Studio", 24).pack(side="left")
    label(header, "OVIC LABS   ·   LOCAL SESSION", 10, ACCENT).pack(side="right")

    stage = tk.Frame(root, bg=BG)
    stage.pack(fill="both", expand=True, padx=28)
    canvas = tk.Canvas(stage, bg="#070c13", highlightthickness=1, highlightbackground=PANEL)
    canvas.pack(side="left", fill="both", expand=True)
    detail = tk.Frame(stage, bg=PANEL, width=270)
    detail.pack(side="right", fill="y", padx=(14, 0))
    detail.pack_propagate(False)
    label(detail, "Observation", 15, bg=PANEL).pack(fill="x", padx=18, pady=(18, 6))
    estimate = label(detail, "Waiting for input", 14, ACCENT, PANEL)
    estimate.pack(fill="x", padx=18)
    metrics = label(detail, "", 11, MUTED, PANEL)
    metrics.configure(justify="left")
    metrics.pack(fill="x", padx=18, pady=12)
    limitation = label(detail, "", 10, MUTED, PANEL)
    limitation.configure(wraplength=230, justify="left")
    limitation.pack(fill="x", padx=18)

    footer = tk.Frame(root, bg=BG)
    footer.pack(fill="x", padx=28, pady=18)
    status = label(footer, "Ready", 11, MUTED)
    status.configure(wraplength=420, justify="left")
    status.pack(side="right", fill="x", expand=True, padx=(16, 0))

    def redraw(_event: object = None) -> None:
        nonlocal preview
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if current.image is None or current.observation is None:
            preview = None
            canvas.create_text(
                width / 2,
                height / 2,
                text="Start camera or open an image",
                fill=MUTED,
                font=("Segoe UI", 16),
            )
            return
        fitted = ImageOps.contain(overlay(current.image, current.observation), (width, height))
        preview = ImageTk.PhotoImage(fitted)
        canvas.create_image(width / 2, height / 2, image=preview)

    canvas.bind("<Configure>", redraw)

    def show(frame: Frame) -> None:
        nonlocal current
        current = frame
        status.configure(text=frame.message)
        obs = frame.observation
        if obs is None:
            estimate.configure(text="Waiting for input")
            metrics.configure(text="")
            limitation.configure(text="")
        else:
            eligible = (
                obs.status.value == "ok"
                and obs.input_quality.value == "acceptable"
                and obs.model_state.value == "MODEL_LOADED_VALIDATED"
                and obs.is_calibrated
                and obs.is_validated
            )
            name = obs.dominant_estimate if eligible else "Estimate withheld"
            confidence = f"{obs.confidence:.0%}" if eligible else "Unavailable"
            estimate.configure(text=name.replace("_", " ").capitalize())
            metrics.configure(
                text=f"Status  {obs.status.value.replace('_', ' ')}\n"
                f"Model  {'Validated' if obs.is_validated else 'Unvalidated'}\n"
                f"Confidence  {confidence}\n"
                f"Signal quality  {obs.quality_score:.0%}\n"
                f"Processing  {obs.processing_latency_ms:.1f} ms"
            )
            limitation.configure(text="\n\n".join(obs.limitations[:3]))
        redraw()

    def poll() -> None:
        if not stop.is_set():
            try:
                show(results.get_nowait())
            except Empty:
                pass
        busy = worker is not None and worker.is_alive()
        start_button.configure(state="disabled" if busy else "normal")
        image_button.configure(state="disabled" if busy else "normal")
        stop_button.configure(state="normal" if busy and not stop.is_set() else "disabled")
        root.after(33, poll)

    def start(source: Path | int) -> None:
        nonlocal worker
        if worker is not None and worker.is_alive():
            return
        while not results.empty():
            results.get_nowait()
        stop.clear()
        show(Frame(message="Opening camera…" if isinstance(source, int) else "Analyzing image…"))

        def work() -> None:
            try:
                asyncio.run(run_source(config, source, stop, results))
            except Exception as exc:
                publish(results, Frame(message=str(exc)))

        worker = threading.Thread(target=work, daemon=True)
        worker.start()

    def open_image() -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*")]
        )
        if path:
            start(Path(path))

    def stop_camera() -> None:
        stop.set()
        show(Frame(message="Capture stopped"))

    def close() -> None:
        stop.set()
        root.destroy()

    def button(text: str, callback: Callable[[], None], active: bool = False) -> tk.Button:
        item = tk.Button(
            footer,
            text=text,
            command=callback,
            padx=14,
            pady=8,
            relief="flat",
            bg=ACCENT if active else PANEL,
            fg=BG if active else TEXT,
            cursor="hand2",
        )
        item.pack(side="left", padx=(0, 8))
        return item

    start_button = button("Start camera", lambda: start(args.camera), active=True)
    stop_button = button("Stop", stop_camera)
    image_button = button("Open image", open_image)
    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    root.mainloop()
    if worker is not None:
        worker.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
