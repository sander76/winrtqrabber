from __future__ import annotations

import logging
from asyncio import Event
from typing import Callable, Optional, Tuple

from winrt.windows.devices.pointofservice import (
    BarcodeScanner,
    BarcodeScannerDataReceivedEventArgs,
    ClaimedBarcodeScanner,
)
from winrt.windows.graphics.imaging import (
    BitmapAlphaMode,
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winrt.windows.media.capture import (
    MediaCapture,
    MediaCaptureInitializationSettings,
    MediaCaptureMemoryPreference,
    MediaCaptureSharingMode,
    MediaStreamType,
    StreamingCaptureMode,
)
from winrt.windows.media.capture.frames import (
    MediaFrameSourceGroup,
    MediaFrameSourceKind,
)
from winrt.windows.security.cryptography import (
    BinaryStringEncoding,
    CryptographicBuffer,
)
from winrt.windows.storage.streams import Buffer

_LOGGER = logging.getLogger(__name__)


async def get_barcode_scanner() -> Optional[BarcodeScanner]:
    _LOGGER.info("Looking for an available barcode scanner.")
    scanner = await BarcodeScanner.get_default_async()
    if scanner:
        _LOGGER.info(
            f"Found a scanner: {scanner} with video id: {scanner.video_device_id}"
        )
    else:
        _LOGGER.info("No webcam barcode scanner found or unable to access.")
    return scanner


async def find_color_source():
    source_groups = await MediaFrameSourceGroup.find_all_async()

    color_source = None
    for group in source_groups:
        # _LOGGER.debug()
        for info in group.source_infos:
            _LOGGER.debug(
                "Available sources: %s ,info %s", info.media_stream_type, info
            )
            if (
                info.media_stream_type == MediaStreamType.VIDEO_RECORD
                and info.source_kind == MediaFrameSourceKind.COLOR.value
            ):
                color_source = info
        return group, color_source


def get_supported_frame_format(color_source):
    formats = color_source.supported_formats

    for format in formats:
        if format.video_format.width <= 800:
            return format


def get_data_string(data) -> str:
    result = CryptographicBuffer.convert_binary_to_string(
        BinaryStringEncoding.UTF8, data
    )
    return result


class WinrtCapture:
    _camera = None
    _media_capture = None
    _media_frame_reader = None
    _barcode_scanner = None
    _ui_update: Optional[Callable[[bytearray], None]] = None
    _scanned: Event
    _result: str

    async def start(self, frame_received_callback: Callable[[bytearray], None],) -> str:
        self._scanned = Event()
        _LOGGER.info("Starting webcam")
        self._ui_update = frame_received_callback
        await self._start_scanner()
        await self._start_preview()
        await self._scanned.wait()
        await self.stop()
        return self._result

    async def prepare_webcam(self) -> Tuple[int, int]:
        """Prepare the webcam.

        Returns:
            A tuple containing the resolution.
        """
        _LOGGER.info("Preparing webcam.")
        await self._prepare_barcode_scanner()
        resolution = await self._prepare_preview(self._barcode_scanner.video_device_id)
        return resolution

    async def _start_preview(self):
        await self._media_frame_reader.start_async()

    async def _prepare_barcode_scanner(self):
        try:
            self._barcode_scanner = await get_barcode_scanner()
            _LOGGER.debug("Claiming the scanner")
            self._camera = await self._barcode_scanner.claim_scanner_async()
            _LOGGER.debug("Adding callback")
            self._camera.add_data_received(self._on_data_received)
            _LOGGER.debug("enabling automatic decoding.")
            self._camera.is_decode_data_enabled = True
            _LOGGER.debug("Start scanning")
            await self._camera.enable_async()
            _LOGGER.debug("finished initializing")

        except Exception as err:
            _LOGGER.exception(err)
            raise err from None

    async def _start_scanner(self):
        """Start the barcode scanner."""
        try:
            await self._camera.start_software_trigger_async()
        except Exception as err:
            _LOGGER.exception(err)

    def _on_data_received(
        self, sender: ClaimedBarcodeScanner, args: BarcodeScannerDataReceivedEventArgs
    ):
        _LOGGER.info("Barcode data scanned")
        try:
            self._result = get_data_string(args.report.scan_data_label)
            _LOGGER.info("result : %s", self._result)
            self._scanned.set()
            _LOGGER.info(get_data_string(args.report.scan_data))
        except Exception as err:
            _LOGGER.exception(err)

    async def _prepare_preview(self, video_device_id) -> Tuple[int, int]:
        self._media_capture = MediaCapture()
        group, color_source = await find_color_source()

        settings = MediaCaptureInitializationSettings()
        settings.video_device_id = video_device_id
        settings.source_group = group
        settings.sharing_mode = MediaCaptureSharingMode.EXCLUSIVE_CONTROL
        settings.memory_preference = MediaCaptureMemoryPreference.CPU
        settings.streaming_capture_mode = StreamingCaptureMode.VIDEO

        await self._media_capture.initialize_async(settings)

        color_frame_source = self._media_capture.frame_sources[color_source.id]
        color_frame_format = get_supported_frame_format(color_frame_source)
        await color_frame_source.set_format_async(color_frame_format)

        self._media_frame_reader = await self._media_capture.create_frame_reader_async(
            color_frame_source
        )
        self._media_frame_reader.add_frame_arrived(self._frame_received)

        return (
            color_frame_format.video_format.width,
            color_frame_format.video_format.height,
        )

    def _frame_received(self, sender, frame):
        """Process an incoming preview frame.

        Turns the data into a bytearray containing bitmap data.
        """
        if self._ui_update is None:
            _LOGGER.error("No ui update callback function defined.")
            return
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

            self._ui_update(b_array)

        except Exception as err:
            _LOGGER.exception(err)

    async def stop(self):
        """Stop scanning."""
        await self._media_frame_reader.stop_async()
        await self._camera.disable_async()
        self._media_frame_reader = None
