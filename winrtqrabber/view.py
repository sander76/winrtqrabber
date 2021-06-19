import logging

import wx

_LOGGER = logging.getLogger(__name__)


class ScannerView(wx.Panel):
    """Panel on which the webcam data is painted."""

    def __init__(
        self,
        parent,
        mirror_x=True,
        width=800,
        height=600,
        style=wx.NO_BORDER,
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
