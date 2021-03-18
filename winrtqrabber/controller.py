import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pyzbar.pyzbar import Decoded
    from winrtqrabber.view import ScannerView

_LOGGER = logging.getLogger(__name__)


class Controller:
    def __init__(self, model, view: "ScannerView"):
        self._model = model
        self.view = view

    async def start_scan(self):
        await self._model.start(self.view.set_frame,)

    def stop_scan(self, result: Optional["Decoded"] = None):
        if result:
            print(result)
