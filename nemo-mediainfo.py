import os
import exifread
import pymediainfo
import urllib.parse

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Nemo", "3.0")

from gi.repository import GObject, Gtk, Nemo  # noqa: E402
# ==============================================================================
GUI = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.24"/>
    <object class="GtkScrolledWindow" id="builder_root_widget">
    <property name="visible">True</property>
    <property name="can-focus">True</property>
    <property name="shadow-type">in</property>
    <child>
        <object class="GtkViewport">
        <property name="visible">True</property>
        <property name="can-focus">False</property>
        <child>
            <object class="GtkTreeView" id="treev">
            <property name="visible">True</property>
            <property name="can-focus">True</property>
            <child internal-child="selection">
                <object class="GtkTreeSelection"/>
            </child>
            </object>
        </child>
        </object>
    </child>
    </object>
</interface>
"""
# ==============================================================================
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60 * 60 * 24),
    ("hour", 60 * 60),
    ("minute", 60),
    ("second", 1)
)
# ==============================================================================
def human_time_duration(seconds) -> str:

    if seconds >= 1:
        parts = []

        for unit, div in TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)

            if amount > 0:
                parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else "s"))

        if len(parts) > 1:
            ret = ", ".join(parts[:-1]) + " and " + parts[-1]
        else:
            ret = parts[0]

    elif 0 < seconds < 1:
        ret = "Less than a second"

    else:
        ret = "Unknown"

    return ret
# ==============================================================================
def track_format_info_to_str(track) -> str:

    str_format_info = ""

    if track.format is not None:
        str_format_info = track.format

        if track.format_info is not None:
            str_format_info += " (" + track.format_info + ")"

        if track.format_profile is not None:
            str_format_info += " (Profile: " + track.format_profile + ")"

    return str_format_info
# ==============================================================================
def track_duration_to_str(track) -> str:

    str_duration = human_time_duration(float(track.duration) / 1000)

    if track.other_duration is not None and len(track.other_duration) >= 4:
        str_duration += " (" + track.other_duration[3] + ")"

    return str_duration
# ==============================================================================
def track_codec_to_str(track) -> str:

    str_codec = ""

    if track.codec_id is not None:
        str_codec = track.codec_id

        if track.codec_id_info is not None:
            str_codec += " (" + track.codec_id_info + ")"

    return str_codec
# ==============================================================================
class MediaFile():

    def __init__(self, filename) -> None:

        self.filename = filename
        self.shortname = os.path.basename(filename)
        self.tracks: list[MediaFileTrack] = []

        if len(self.shortname) > 30:
            self.shortname = self.shortname[:30] + "..."
# ==============================================================================
class MediaFileTrack():

    def __init__(self, name) -> None:

        self.name = name
        self.properties: list[MediaFileTrackProperty] = []

    def append(self, name, value) -> None:

        if value == None:
            return

        self.properties.append(MediaFileTrackProperty(name, value))
# ==============================================================================
class MediaFileTrackProperty():

    def __init__(self, name, value) -> None:

        self.name = name
        self.value = value
# ==============================================================================
class TrackHEIC():

    def __init__(self, exifTags) -> None:

        self.track_type = "Image"
        self.format = "HEIC"
        self.width = exifTags["Image ImageWidth"]
        self.height = exifTags["Image ImageLength"]
        self.color_space = exifTags["EXIF ColorSpace"]

        self.bit_depth = None
        self.compression_mode = None
# ==============================================================================
class MediaInfoHEIC():

    def __init__(self, exifTags) -> None:

        self.tracks = [TrackHEIC(exifTags)]
# ==============================================================================
class MediaPropertyPage(GObject.GObject, Nemo.PropertyPageProvider, Nemo.NameAndDescProvider):

    def get_property_pages(self, files) -> list[Nemo.PropertyPage]:

        actual_files = []

        for file in files:
            if file.get_uri_scheme() != "file":
                continue

            if file.is_directory():
                continue

            filename = urllib.parse.unquote(file.get_uri()[7:])

            _, extension = os.path.splitext(os.path.basename(filename))
            extension = extension.lower()

            exifTags = self.getExifTags(filename)

            mediaInfo = None

            if extension == ".heic":
                if exifTags:
                    mediaInfo = MediaInfoHEIC(exifTags)
            else:
                mediaInfo = pymediainfo.MediaInfo.parse(filename)

            if mediaInfo is None:
                return []

            media_file = MediaFile(filename)

            for track in mediaInfo.tracks:
                if track.track_type == "General":
                    media_track = MediaFileTrack("General")

                    if track.track_name is not None:
                        media_track.append("Title", track.track_name)

                    if track.performer is not None:
                        media_track.append("Artist", track.performer)

                    if track.album is not None:
                        media_track.append("Album", track.album)

                    if track.genre is not None:
                        media_track.append("Genre", track.genre)

                    if track.comment is not None:
                        media_track.append("Comment", track.comment)

                    if len(media_track.properties) > 0:
                        media_file.tracks.append(media_track)

                elif track.track_type == "Video":
                    media_track = MediaFileTrack("Video")

                    fps = float(track.frame_rate)

                    if fps.is_integer():
                        fps = int(fps)

                    str_format_info = track_format_info_to_str(track)

                    if str_format_info != "":
                        media_track.append("Format", str_format_info)

                    if track.internet_media_type is not None:
                        media_track.append("Internet media type", track.internet_media_type)

                    str_codec = track_codec_to_str(track)

                    if str_codec != "":
                        media_track.append("Codec", str_codec)

                    media_track.append("Frame rate", str(fps) + " FPS (" + str(track.frame_rate_mode) + ")")

                    media_track.append("Size (pixels)", str(track.width) +
                                       " (width) x " + str(track.height) + " (height)")

                    if track.other_display_aspect_ratio is not None:
                        media_track.append("Aspect ratio", ", ".join(track.other_display_aspect_ratio))

                    media_track.append("Duration", track_duration_to_str(track))

                    if track.bit_rate is not None:
                        media_track.append("Bit rate", str(track.bit_rate / 1000) + " kbps")

                    if track.bit_depth is not None:
                        media_track.append("Bit depth", str(track.bit_depth) + " bits")

                    if track.scan_type is not None:
                        media_track.append("Scan type", str(track.scan_type))

                    media_track.append("Compression mode", track.compression_mode)

                    media_file.tracks.append(media_track)

                elif track.track_type == "Audio":
                    media_track = MediaFileTrack("Audio")

                    str_format_info = track_format_info_to_str(track)

                    if str_format_info != "":
                        media_track.append("Format", str_format_info)

                    if track.internet_media_type is not None:
                        media_track.append("Internet media type", track.internet_media_type)

                    if track.commercial_name is not None and track.commercial_name != track.format:
                        media_track.append("Commercial name", track.commercial_name)

                    str_codec = track_codec_to_str(track)

                    if str_codec != "":
                        media_track.append("Codec", str_codec)

                    media_track.append("Mode", track.mode)

                    media_track.append("Channels", track.channel_s)

                    if track.channel_layout is not None:
                        media_track.append("Channels layout", track.channel_layout)

                    if track.channel_positions is not None:
                        media_track.append("Channels positions", track.channel_positions)

                    media_track.append("Duration", track_duration_to_str(track))

                    media_track.append("Sampling rate", str(track.sampling_rate) + " Hz")

                    if track.samples_per_frame is not None:
                        media_track.append("Samples per frame", track.samples_per_frame)

                    if track.bit_rate is not None:
                        media_track.append("Bit rate", str(track.bit_rate / 1000) + " kbps")

                    if track.bit_rate_mode is not None:
                        media_track.append("Bit rate mode", track.bit_rate_mode)

                    media_track.append("Compression mode", track.compression_mode)

                    media_file.tracks.append(media_track)

                elif track.track_type == "Image":
                    media_track = MediaFileTrack("Image")

                    media_track.append("Format", track.format)

                    media_track.append("Size (pixels)", str(track.width) +
                                       " (width) x " + str(track.height) + " (height)")

                    if track.bit_depth is not None:
                        media_track.append("Bit depth", str(track.bit_depth) + " bits")

                    media_track.append("Color space", track.color_space)

                    if track.compression_mode is not None:
                        media_track.append("Compression mode", track.compression_mode)

                    media_file.tracks.append(media_track)

                    if (exifTags is not None) and (len(exifTags) > 0):
                        exif_media_track = MediaFileTrack("Image EXIF Data")

                        for tag, tagValue in exifTags.items():
                            if tag in ("JPEGThumbnail",
                                       "TIFFThumbnail",
                                       "Filename",
                                       "EXIF MakerNote",
                                       "EXIF UserComment",
                                       "EXIF ColorSpace",
                                       "Image ImageWidth",
                                       "Image ImageLength",
                                       "EXIF ExifImageWidth",
                                       "EXIF ExifImageLength"
                                       ):
                                continue

                            exif_media_track.append(tag, tagValue)

                        media_file.tracks.append(exif_media_track)

            if len(media_file.tracks) == 0:
                continue

            actual_files.append(media_file)

        if len(actual_files) == 0:
            return []

        self.property_label = Gtk.Label("Media")
        self.property_label.show()

        self.builder = Gtk.Builder()
        self.builder.add_from_string(GUI)

        self.treev: Gtk.TreeView = self.builder.get_object("treev")

        self.store = Gtk.TreeStore(str, str)
        self.treev.set_model(self.store)

        for file in actual_files:
            fileparent = None

            if len(actual_files) > 1:
                fileparent = self.store.append(None, [file.shortname, ""])

            for media_track in file.tracks:
                storetrack: Gtk.TreeIter = self.store.append(fileparent, [media_track.name, ""])

                for prop in media_track.properties:
                    self.store.append(storetrack, [prop.name, str(prop.value)])

        self.treev.expand_all()

        for i, column_title in enumerate(["Property", "Value"]):
            if i == 0:
                renderer = Gtk.CellRendererText(weight_set=True, weight=600)
            else:
                renderer = Gtk.CellRendererText()

            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_resizable(True)
            self.treev.append_column(column)

        return [
            Nemo.PropertyPage(
                name="NemoPython::media",
                label=self.property_label,
                page=self.builder.get_object("builder_root_widget")
            )
        ]

    def get_name_and_desc(self) -> list[str]:

        return ["Nemo Media Tab:::View video/audio/image information from the properties tab in Nemo."]

    def getExifTags(self, filePath):
        try:
            with open(filePath, "rb") as fData:
                tags = exifread.process_file(fData)
                return tags
        except Exception as e:
            return None
# ==============================================================================
