import logging

import wx
from winrt.windows.graphics.imaging import (
    BitmapAlphaMode,
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winrt.windows.security.cryptography import CryptographicBuffer
from winrt.windows.storage.streams import Buffer

_LOGGER = logging.getLogger(__name__)


class ScannerView(wx.Panel):
    """Panel on which the webcam data is painted."""

    def __init__(
        self,
        parent,
        mirror_x=True,
        mirror_y=True,
        width=800,
        height=600,
        style=wx.NO_BORDER,
    ):
        """

        Args:
            parent: wx parent.
            mirror_x: Flip image on its x axis.
            mirror_y: Flip image on its y axis.
            width: width of this panel.
            height: height of this panel.
            style: a style.
        """

        wx.Panel.__init__(self, parent, size=(width, height), style=style)

        self.width = width
        self.height = height

        self.buffer = wx.NullBitmap

        self._mirror_x = mirror_x
        self._mirror_y = mirror_y

        # client_dc = wx.WindowDC(self)
        self._matrix = wx.AffineMatrix2D()
        self._matrix.Translate(dx=640, dy=0)
        self._matrix.Scale(
            -1, 1
        )  # this should be (-1,1) to allow for horizontal flip. But that does not work.
        # client_dc.SetTransformMatrix(self._matrix)
        self._buffered_dc = wx.BufferedDC(
            wx.ClientDC(self), wx.NullBitmap, wx.BUFFER_VIRTUAL_AREA
        )

    def on_show(self, event):
        if event.IsShown():
            self.GetParent().Layout()
            self.Layout()

    def set_frame(self, sender, frame):
        """Populate the image with raw data."""

        try:
            # _LOGGER.debug("populating view.")
            last_frame = sender.try_acquire_latest_frame()
            if last_frame is None:
                return
            video_frame = last_frame.video_media_frame
            bitmap: SoftwareBitmap = video_frame.software_bitmap
        except Exception as err:
            _LOGGER.exception(err)
            return
            # raise err from None

        bitmap = SoftwareBitmap.convert(
            bitmap, BitmapPixelFormat.RGBA8, BitmapAlphaMode.PREMULTIPLIED
        )

        try:
            length = 4 * bitmap.pixel_height * bitmap.pixel_width
            buffer = Buffer(length)
            bitmap.copy_to_buffer(buffer)

            b_array = bytearray(CryptographicBuffer.copy_to_byte_array(buffer))

            self.buffer = wx.Bitmap.FromBufferRGBA(
                bitmap.pixel_width, bitmap.pixel_height, b_array
            )

            client_cd = wx.WindowDC(self)
            client_cd.SetTransformMatrix(self._matrix)

            try:
                wx.BufferedDC(client_cd, self.buffer, wx.BUFFER_VIRTUAL_AREA)
            except Exception as err:
                _LOGGER.exception(err)

        except Exception as err:
            _LOGGER.exception(err)
