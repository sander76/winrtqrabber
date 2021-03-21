import logging

from winrt.windows.devices.enumeration import DeviceClass, DeviceInformation
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

    return devices[0]


def on_fail(*args, **kwargs):
    print("failed")


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

    async def _find_camera(self):
        self._camera = await find_camera()

    async def start(self, frame_received_callback):
        _LOGGER.info("Starting webcam")
        await self._find_camera()
        group, color_source = await find_color_source()

        self._media_capture = MediaCapture()

        settings = MediaCaptureInitializationSettings()
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
