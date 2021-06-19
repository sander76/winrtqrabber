from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import wx
from aio_wx_widgets.panels import panel
from aio_wx_widgets.widgets.button import AioButton
from aio_wx_widgets.widgets.text import Text

if TYPE_CHECKING:
    from winrtqrabber.controller import Controller
_LOGGER = logging.getLogger(__name__)


class TheView(panel.SimplePanel["Controller"]):
    def __init__(self, parent: wx.Panel, controller: Controller):
        super().__init__(parent, controller)

        self.scanner_view = ScannerView(parent=self.ui_item, width=650, height=480)
        self.add(self.scanner_view, create=False)
        self.add(AioButton("start", self._on_start))  # type: ignore
        self.add(AioButton("stop", self._on_stop))  # type: ignore
        self.add(Text(binding=self.bind("scan_result")))

    async def _on_start(self, event):  # type: ignore
        await self.controller.setup_scanner()
        self.scanner_view.set_preview_size(*self.controller.resolution)

        await self.controller.start_scan(self.scanner_view.set_frame)

    async def _on_stop(self, event):  # type: ignore
        _LOGGER.info("Stopping")
        await self.controller.stop_scan()


class ScannerView(wx.Panel):
    """Panel on which the webcam data is painted."""

    def __init__(
        self,
        parent,
        mirror_x: bool = True,
        width: int = 800,
        height: int = 600,
        style: int = wx.NO_BORDER,
    ):
        """

        Args:
            parent: wx parent.
            mirror_x: Flip image on its x axis.
            width: width of this panel.
            height: height of this panel.
            style: a style.
        """

        wx.Panel.__init__(self, parent, size=(width, height), style=style)

        self.width = None
        self.height = None

        self.buffer = wx.NullBitmap

        self._mirror_x = mirror_x

        self._matrix = wx.AffineMatrix2D()
        self._buffered_dc = wx.BufferedDC(
            wx.ClientDC(self), wx.NullBitmap, wx.BUFFER_VIRTUAL_AREA
        )

    def on_show(self, event):
        if event.IsShown():
            self.GetParent().Layout()
            self.Layout()

    def set_preview_size(self, width, height):
        self.width = width
        self.height = height

        if self._mirror_x:
            self._matrix.Translate(dx=self.width, dy=0)
            self._matrix.Scale(-1, 1)

    def set_frame(self, bitmapdata: bytearray):
        """Populate the image with raw data."""

        self.buffer = wx.Bitmap.FromBufferRGBA(self.width, self.height, bitmapdata)

        client_cd = wx.WindowDC(self)
        client_cd.SetTransformMatrix(self._matrix)

        try:
            wx.BufferedDC(client_cd, self.buffer, wx.BUFFER_VIRTUAL_AREA)
        except Exception as err:
            _LOGGER.exception(err)
