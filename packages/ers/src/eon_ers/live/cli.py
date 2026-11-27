"""Command-line interface to launch the ERS live sensory demonstration server."""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser

import uvicorn

from eon_ers.config import ERSConfig
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.live.server import create_live_app


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the ERS live demonstration server."""
    parser = argparse.ArgumentParser(
        prog="eon-ers-live",
        description="OVIC EON ERS Live Sensory Demonstration Server (Webcam & Microphone)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind the server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to bind the server (default: 8000)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level for uvicorn (default: info)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        default=False,
        help="Automatically open the live demonstration dashboard in the default browser",
    )
    parser.add_argument(
        "--facial-model",
        type=str,
        help="Optional path to a facial ONNX model (requires the ml extra)",
    )
    parser.add_argument(
        "--speech-model",
        type=str,
        help="Optional path to a speech ONNX model (requires the ml extra)",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Main CLI entrypoint for launching the ERS live demonstration."""
    parsed = parse_args(args)

    config = ERSConfig(
        facial_model_path=parsed.facial_model,
        speech_model_path=parsed.speech_model,
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
    )
    engine = ERSEngine(config)
    session_manager = LiveSessionManager(engine)
    app = create_live_app(engine=engine, session_manager=session_manager)

    url = f"http://{parsed.host}:{parsed.port}"
    print("=" * 70)
    print("  OVIC EON — Emotion Recognition System (ERS) Live Demonstration")
    print("=" * 70)
    print(f"Server address:   {url}")
    print(f"Dashboard URL:    {url}/")
    print(f"Health check:     {url}/api/health")
    print(f"WebSocket stream: ws://{parsed.host}:{parsed.port}/ws/live/{{session_id}}")
    print("-" * 70)
    print("Privacy Guarantee: Epistemic modesty invariants active. Zero media retention.")
    print("=" * 70)

    server = uvicorn.Server(
        uvicorn.Config(app, host=parsed.host, port=parsed.port, log_level=parsed.log_level)
    )
    stopped = threading.Event()
    if parsed.open_browser:

        def _open() -> None:
            while not stopped.wait(0.1):
                if server.started:
                    webbrowser.open(url)
                    return

        threading.Thread(target=_open, daemon=True).start()

    try:
        server.run()
        return 0 if server.started else 1
    except KeyboardInterrupt:
        print("\n[INFO] Demonstration server stopped cleanly by user.")
        return 0
    except Exception as exc:
        print(f"\n[ERROR] Server failed: {exc}", file=sys.stderr)
        return 1
    finally:
        stopped.set()


if __name__ == "__main__":
    sys.exit(main())
