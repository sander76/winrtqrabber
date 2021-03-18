import logging

import wx
from winrt.windows.graphics.imaging import (
    BitmapAlphaMode,
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winrt.windows.storage.streams import Buffer, DataReader

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
        self._buffered_dc = wx.BufferedDC(
            wx.ClientDC(self), wx.NullBitmap, wx.BUFFER_VIRTUAL_AREA
        )

    def on_show(self, event):
        if event.IsShown():
            self.GetParent().Layout()
            self.Layout()

    def set_frame(self, sender, frame):
        """Populate the image with raw data."""

        # print(f"getting frame: {frame}")
        try:
            last_frame = sender.try_acquire_latest_frame()
            video_frame = last_frame.video_media_frame

            bitmap: SoftwareBitmap = video_frame.software_bitmap
        except Exception as err:
            _LOGGER.exception(err)
            raise err from None

        bitmap = SoftwareBitmap.convert(
            bitmap, BitmapPixelFormat.RGBA8, BitmapAlphaMode.PREMULTIPLIED
        )

        try:
            length = 4 * bitmap.pixel_height * bitmap.pixel_width
            buffer = Buffer(length)
            bitmap.copy_to_buffer(buffer)

            reader = DataReader.from_buffer(buffer)
            bt = bytes((reader.read_byte() for _ in range(length)))

            self.buffer = wx.Bitmap.FromBufferRGBA(
                bitmap.pixel_width, bitmap.pixel_height, bt
            )
            wx.BufferedDC(wx.ClientDC(self), self.buffer, wx.BUFFER_VIRTUAL_AREA)

        except Exception as err:
            _LOGGER.exception(err)
