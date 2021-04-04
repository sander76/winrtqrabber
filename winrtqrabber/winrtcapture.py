import logging

from winrt.windows.devices.enumeration import DeviceClass, DeviceInformation
from winrt.windows.devices.pointofservice import (
    BarcodeScanner,
    BarcodeScannerDataReceivedEventArgs,
    ClaimedBarcodeScanner,
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

_LOGGER = logging.getLogger(__name__)


async def find_camera():
    # di = DeviceInformation()

    devices = await DeviceInformation.find_all_async(DeviceClass.VIDEO_CAPTURE)
    device = devices[0]
    _LOGGER.info(f"Found a webcam {device} with id {device.id}")
    return devices[0]


async def get_barcode_scanner() -> BarcodeScanner:
    # web_cam = await find_camera()
    # scanner = await BarcodeScanner.from_id_async(web_cam.id)
    _LOGGER.info("Looking for an available barcode scanner.")
    scanner = await BarcodeScanner.get_default_async()
    _LOGGER.debug(
        f"Found a scanner: {scanner} with video id: {scanner.video_device_id}"
    )
    return scanner


async def find_color_source():
    source_groups = await MediaFrameSourceGroup.find_all_async()

    color_source = None
    for group in source_groups:
        for info in group.source_infos:
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


class WinrtCapture:
    _camera = None
    _media_capture = None
    _media_frame_reader = None

    async def _find_camera(self) -> str:
        try:
            camera = await get_barcode_scanner()
            _LOGGER.debug("Claiming the scanner")
            self._camera = await camera.claim_scanner_async()

            _LOGGER.debug("Adding callback")
            self._camera.add_data_received(self._on_data_received)
            _LOGGER.debug("enabling automatic decoding.")
            self._camera.is_decode_data_enabled = True
            _LOGGER.debug("Start scanning")
            await self._camera.enable_async()
            _LOGGER.debug("finished initializing")

            # this command activates the actual webcam. Without it, this does not work.
            # await self._camera.show_video_preview_async()
            await self._camera.start_software_trigger_async()
            # await self.start_capturing(camera.video_device_id)

            # await self.create_frame_reader(camera.video_device_id)

        except Exception as err:
            _LOGGER.exception(err)
        else:
            return camera.video_device_id

    def _on_data_received(
        self, sender: ClaimedBarcodeScanner, args: BarcodeScannerDataReceivedEventArgs
    ):
        try:
            _LOGGER.info("Barcode data scanned")
            print(args.report.scan_data_label)
            print(f"data: {args.report.scan_data}")
        except Exception as err:
            _LOGGER.exception(err)

    # async def start_capturing(self,video_device_id:str):
    #     self._media_capture=MediaCapture()
    #     settings = MediaCaptureInitializationSettings()
    #     settings.video_device_id=video_device_id
    #     settings.streaming_capture_mode=StreamingCaptureMode.VIDEO
    #     settings.sharing_mode=MediaCaptureSharingMode.SHARED_READ_ONLY
    #
    #     await self._media_capture.initialize_async(settings)
    #
    #     memory_stream = InMemoryRandomAccessStream()
    #     encoding_profile=MediaEncodingProfile.
    #     encoding_profile= await MediaEncodingProfile.create_from_stream_async(memory_stream)
    #
    #
    #     await self._media_capture.start_recode_to_stream_async(encoding_profile,memory_stream)

    async def start(self, frame_received_callback):
        _LOGGER.info("Starting webcam")
        device_id = await self._find_camera()
        # await asyncio.sleep(4)
        await self.create_frame_reader(device_id, frame_received_callback)
        #
        # self._media_capture = MediaCapture()

    async def create_frame_reader(self, video_device_id, frame_received_callback):
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
        self._media_frame_reader.add_frame_arrived(frame_received_callback)

        await self._media_frame_reader.start_async()

    async def stop(self):
        await self._media_frame_reader.stop_async()
        self._media_capture.dispose()


# def frame_received_callback(sender, frame):
#     print(frame)


#
# async def capture(on_arrived_call_back):
#     group, color_source = await find_color_source()
#     webcam = await find_camera()
#     print(webcam)
#
#     mediacapture = MediaCapture()
#
#     settings = MediaCaptureInitializationSettings()
#     settings.source_group = group
#     settings.sharing_mode = MediaCaptureSharingMode.EXCLUSIVE_CONTROL
#     settings.memory_preference = MediaCaptureMemoryPreference.CPU
#     settings.streaming_capture_mode = StreamingCaptureMode.VIDEO
#
#     await mediacapture.initialize_async(settings)
#
#     color_frame_source = mediacapture.frame_sources[color_source.id]
#     color_frame_format = get_supported_frame_format(color_frame_source)
#
#     await color_frame_source.set_format_async(color_frame_format)
#
#     frame_reader = await mediacapture.create_frame_reader_async(color_frame_source)
#     frame_reader.add_frame_arrived(on_arrived_call_back)
#
#     await frame_reader.start_async()
#     print("capturing")
#     await asyncio.sleep(10)
#
#
# if __name__ == "__main__":
#
#     def on_arrived(sender, arrived_frame):
#         print(arrived_frame)
#
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(capture(on_arrived))
#     # capture()
