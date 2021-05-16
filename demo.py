import asyncio
import logging

import wx
from aio_wx_widgets.frame import DefaultFrame
from aio_wx_widgets.widgets import button, text
from winrtqrabber.controller import Controller
from winrtqrabber.view import ScannerView
from winrtqrabber.winrtcapture import WinrtCapture
from wxasync import WxAsyncApp

_LOGGER = logging.getLogger(__name__)


class MainWindow(DefaultFrame):
    def __init__(self):
        super().__init__("Main window")
        model = WinrtCapture()

        view = ScannerView(self, width=650, height=480)

        self.controller = Controller(model, view)
        self.add(view, layout=wx.ALIGN_CENTER, create=False)

        self.add(button.async_button("start", self._on_start))
        self.add(button.async_button("stop", self._on_stop))

        self.scan_results: text.Text = self.add(text.Text("unknown"))

    async def _on_start(self, event):
        result = await self.controller.start_scan()
        if result:
            self.scan_results.set_text(result)

    async def _on_stop(self, event):
        _LOGGER.info("Stopping")
        await self.controller.stop_scan()


if __name__ == "__main__":
    # os.environ["DEBUGGING"] = "1"
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    app = WxAsyncApp()
    main_window = MainWindow()
    main_window.Show()
    app.SetTopWindow(main_window)
    loop.run_until_complete(app.MainLoop())
