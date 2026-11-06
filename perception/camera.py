"""Camera perception module.

Captures frames from a camera device using OpenCV, applies rate limiting,
and publishes ``camera.frame`` events on the event bus. Designed to work
without hardware (mock/monkeypatched capture) so tests pass offline.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import cv2
import numpy as np
from core.event_bus import EventBus


class Camera:
    """Camera frame capture with rate limiting.

    Parameters
    ----------
    event_bus:
        Event bus to publish ``camera.frame`` events on.
    device_index:
        OpenCV camera device index (0 = Integrated Webcam by default).
    width:
        Frame width in pixels.
    height:
        Frame height in pixels.
    fps:
        Maximum frames per second to capture (rate limiting).
    indicator_enabled:
        Whether to print a console line when the camera is active.
    """

    def __init__(
        self,
        event_bus: EventBus,
        device_index: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 15,
        indicator_enabled: bool = True,
    ) -> None:
        self.event_bus = event_bus
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.indicator_enabled = indicator_enabled
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._on_frame: list[Callable[[np.ndarray, dict], None]] = []
        self._frame_count = 0
        self._last_frame_time: Optional[float] = None

    def start(self) -> None:
        """Open the camera and start the capture loop in a background thread."""
        if self._running:
            return
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            self._cap = None
            raise RuntimeError(f"Cannot open camera device {self.device_index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        if self.indicator_enabled:
            print(f"[camera] active on device {self.device_index}")

    def stop(self) -> None:
        """Stop the capture loop and release the camera."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self.indicator_enabled:
            print(f"[camera] stopped (captured {self._frame_count} frames)")

    def register_frame_callback(self, cb: Callable[[np.ndarray, dict], None]) -> None:
        """Register a callback to run when a frame is captured."""
        self._on_frame.append(cb)

    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame synchronously. Returns None if camera not open."""
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def _capture_loop(self) -> None:
        """Background capture loop with rate limiting."""
        min_interval = 1.0 / self.fps if self.fps > 0 else 0.0
        while self._running:
            t0 = time.monotonic()
            frame = self.capture_frame()
            if frame is not None:
                self._frame_count += 1
                elapsed = (
                    t0 - self._last_frame_time
                    if self._last_frame_time is not None
                    else None
                )
                self._last_frame_time = t0
                meta = {
                    "device_index": self.device_index,
                    "frame_index": self._frame_count,
                    "timestamp": t0,
                    "interval_seconds": elapsed,
                    "shape": frame.shape,
                }
                self.event_bus.publish("camera.frame", {"frame": frame, "meta": meta})
                for cb in list(self._on_frame):
                    try:
                        cb(frame, meta)
                    except Exception:  # noqa: BLE001 - frame callbacks must not crash capture
                        pass
            # Rate limit
            if min_interval > 0:
                elapsed = time.monotonic() - t0
                sleep = min_interval - elapsed
                if sleep > 0:
                    time.sleep(sleep)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def avg_fps(self) -> float:
        """Approximate average FPS based on frame interval measurements."""
        # We don't track all intervals; return the configured fps as a proxy.
        return self.fps
