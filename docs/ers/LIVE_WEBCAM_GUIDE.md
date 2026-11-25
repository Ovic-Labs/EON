# Live Webcam Integration Guide

## Capture Architecture
The Live ERS view in `eon_ers.live.dashboard` uses browser `navigator.mediaDevices.getUserMedia({ video: ... })` only after explicit user interaction ("Start Webcam") and consent registration.

## Features
- Explicit camera device selector (`enumerateDevices()`).
- Configurable target FPS (`0.5`–`10` FPS) and capture resolution (`320x240`, `640x480`).
- JPEG frame encoding over bounded WebSocket (`/ws/live/{session_id}` or `/api/v1/live/sessions/{session_id}/stream`) using `image_base64` and `consent_reference`.
- Backpressure protection via bounded `asyncio.Queue(maxsize=max_ws_queue_size)` so overload drops excess queued frames rather than exhausting RAM.
- Immediate camera track shutdown and server stream termination when **Revoke Consent** is triggered.

## Manual Hardware Qualification Checklist
Before claiming webcam readiness on physical hardware, record:
1. Host OS, browser, USB/integrated camera hardware model.
2. Start camera -> confirm active video preview, WebSocket `frame` messages, facial observation latency.
3. Unplug/disconnect camera -> confirm graceful error state without server crash.
4. Click Pause -> verify capture pauses; click Resume -> verify frames resume.
5. Click Revoke Consent -> verify hardware tracks stop and backend returns `consent_rejected`.
