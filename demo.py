import asyncio
import logging

from aio_wx_widgets.frame import DefaultFrame
from winrtqrabber.controller import Controller
from winrtqrabber.view import TheView
from winrtqrabber.winrtcapture import WinrtCapture
from wxasync import WxAsyncApp

_LOGGER = logging.getLogger(__name__)


class MainWindow(DefaultFrame):
    def __init__(self):
        super().__init__("Main window")

        model = WinrtCapture()

        controller = Controller(model)
        self.view = TheView(self, controller)
        self.view.populate()


if __name__ == "__main__":
    # os.environ["DEBUGGING"] = "1"
    _LOGGER.info("Starting application")
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    app = WxAsyncApp()
    main_window = MainWindow()
    main_window.Show()
    app.SetTopWindow(main_window)
    loop.run_until_complete(app.MainLoop())
