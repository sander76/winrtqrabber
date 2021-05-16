import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from winrtqrabber.view import ScannerView

_LOGGER = logging.getLogger(__name__)


class Controller:
    def __init__(self, model, view: "ScannerView"):
        self._model = model
        self.view = view

    async def start_scan(self) -> str:
        resolution = await self._model.prepare_webcam()
        self.view.set_preview_size(*resolution)
        return await self._model.start(self.view.set_frame)

    async def stop_scan(self):
        await self._model.stop()
