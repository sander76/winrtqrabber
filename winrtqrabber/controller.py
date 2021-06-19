from __future__ import annotations

from typing import Callable

from winrtqrabber.winrtcapture import WinrtCapture


class Controller:
    def __init__(self, model: WinrtCapture):
        self._model = model
        self.resolution = None

        # bindable property
        self.scan_result = "unknown."

    async def setup_scanner(self):
        self.resolution = await self._model.prepare_webcam()

    async def start_scan(self, ui_frame_updater: Callable[[bytearray], None]) -> str:

        self.scan_result = await self._model.start(ui_frame_updater)
        return self.scan_result

    async def stop_scan(self):
        await self._model.stop()
