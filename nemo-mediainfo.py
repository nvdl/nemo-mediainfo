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
def human_time_duration(seconds):

    if seconds == 0:
        return "inf"

    parts = []

    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)

        if amount > 0:
            parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else "s"))

    ret = ", ".join(parts[:-1]) + " and " + parts[-1]

    return ret
# ==============================================================================
def track_format_info_to_str(track):

    str_format_info = None

    if track.format is not None:
        str_format_info = track.format

        if track.format_info is not None:
            str_format_info += " (" + track.format_info + ")"

    return str_format_info
# ==============================================================================
def track_duration_to_str(track):

    str_duration = human_time_duration(float(track.duration) / 1000)

    if track.other_duration is not None and len(track.other_duration) >= 4:
        str_duration += " (" + track.other_duration[3] + ")"

    return str_duration
# ==============================================================================
def track_codec_to_str(track):

    str_codec = None

    if track.codec_id is not None:
        str_codec = track.codec_id

        if track.codec_id_info is not None:
            str_codec += " (" + track.codec_id_info + ")"

    return str_codec
# ==============================================================================
class MediaFile():

    def __init__(self, filename, shortname):

        self.filename = filename
        self.shortname = shortname
        self.tracks = []
# ==============================================================================
class MediaFileTrack():

    def __init__(self, name):

        self.name = name
        self.properties = []

    def append(self, name, value):

        if value == None:
            return

        self.properties.append(MediaFileTrackProperty(name, value))
# ==============================================================================
class MediaFileTrackProperty():

    def __init__(self, name, value):

        self.name = name
        self.value = value
# ==============================================================================
class MediaPropertyPage(GObject.GObject, Nemo.PropertyPageProvider, Nemo.NameAndDescProvider):

    def get_property_pages(self, files):

        actual_files = []

        for i in files:
            if i.get_uri_scheme() != "file":
                continue

            if i.is_directory():
                continue

            filename = urllib.parse.unquote(i.get_uri()[7:])
            mediainfo = pymediainfo.MediaInfo.parse(filename)

            mediafile = MediaFile(filename, os.path.basename(filename))

            if len(mediafile.shortname) > 30:
                mediafile.shortname = mediafile.shortname[:30] + "..."

            for track in mediainfo.tracks:
                if track.track_type == "General":
                    mediatrack = MediaFileTrack("General")

                    if track.track_name is not None:
                        mediatrack.append("Title", track.track_name)

                    if track.performer is not None:
                        mediatrack.append("Artist", track.performer)

                    if track.album is not None:
                        mediatrack.append("Album", track.album)

                    if track.genre is not None:
                        mediatrack.append("Genre", track.genre)

                    if track.comment is not None:
                        mediatrack.append("Comment", track.comment)

                    if len(mediatrack.properties) > 0:
                        mediafile.tracks.append(mediatrack)

                elif track.track_type == "Video":
                    mediatrack = MediaFileTrack("Video")

                    fps = float(track.frame_rate)

                    if fps.is_integer():
                        fps = int(fps)

                    str_format_info = track_format_info_to_str(track)

                    if str_format_info is not None:
                        mediatrack.append("Format", str_format_info)

                    if track.format_profile is not None:
                        mediatrack.append("Format profile", track.format_profile)

                    if track.internet_media_type is not None:
                        mediatrack.append("Internet media type", track.internet_media_type)

                    str_codec = track_codec_to_str(track)

                    if str_codec is not None:
                        mediatrack.append("Codec", str_codec)

                    mediatrack.append("Frame rate", str(fps) + " FPS (" + str(track.frame_rate_mode) + ")")

                    mediatrack.append("Width", str(track.width) + " pixels")
                    mediatrack.append("Height", str(track.height) + " pixels")

                    if track.other_display_aspect_ratio is not None:
                        mediatrack.append("Aspect ratio", ", ".join(track.other_display_aspect_ratio))

                    mediatrack.append("Duration", track_duration_to_str(track))

                    if track.bit_rate is not None:
                        mediatrack.append("Bit rate", str(track.bit_rate / 1000) + " kbps")

                    mediatrack.append("Bit depth", str(track.bit_depth) + " bits")
                    mediatrack.append("Scan type", str(track.scan_type))
                    mediatrack.append("Compression mode", track.compression_mode)

                    mediafile.tracks.append(mediatrack)

                elif track.track_type == "Audio":
                    mediatrack = MediaFileTrack("Audio")

                    str_format_info = track_format_info_to_str(track)

                    if str_format_info is not None:
                        mediatrack.append("Format", str_format_info)

                    if track.format_profile is not None:
                        mediatrack.append("Format profile", track.format_profile)

                    if track.internet_media_type is not None:
                        mediatrack.append("Internet media type", track.internet_media_type)

                    if track.commercial_name is not None and track.commercial_name != track.format:
                        mediatrack.append("Commercial name", track.commercial_name)

                    str_codec = track_codec_to_str(track)

                    if str_codec is not None:
                        mediatrack.append("Codec", str_codec)

                    mediatrack.append("Mode", track.mode)

                    mediatrack.append("Channels", track.channel_s)

                    if track.channel_layout is not None:
                        mediatrack.append("Channels layout", track.channel_layout)

                    if track.channel_positions is not None:
                        mediatrack.append("Channels positions", track.channel_positions)

                    mediatrack.append("Duration", track_duration_to_str(track))

                    mediatrack.append("Sampling rate", str(track.sampling_rate) + " Hz")

                    if track.samples_per_frame is not None:
                        mediatrack.append("Samples per frame", track.samples_per_frame)

                    if track.bit_rate is not None:
                        mediatrack.append("Bit rate", str(track.bit_rate / 1000) + " kbps")

                    if track.bit_rate_mode is not None:
                        mediatrack.append("Bit rate mode", track.bit_rate_mode)

                    mediatrack.append("Compression mode", track.compression_mode)

                    mediafile.tracks.append(mediatrack)

                elif track.track_type == "Image":
                    mediatrack = MediaFileTrack("Image")

                    mediatrack.append("Format", track.format)
                    mediatrack.append("Width", str(track.width) + " pixels")
                    mediatrack.append("Height", str(track.height) + " pixels")
                    mediatrack.append("Bit depth", str(track.bit_depth) + " bits")
                    mediatrack.append("Color space", track.color_space)
                    mediatrack.append("Color space (ICC)", track.colorspace_icc)
                    mediatrack.append("Compression mode", track.compression_mode)

                    mediafile.tracks.append(mediatrack)

                    with open(filename, "rb") as fData:
                        tags = exifread.process_file(fData)

                    if len(tags) > 0:
                        mediatrack.append("Camera brand", tags.get("Image Make", None))
                        mediatrack.append("Camera model", tags.get("Image Model", None))
                        mediatrack.append("Date taken", tags.get("Image DateTime", None))

                        if "EXIF ExposureTime" in tags:
                            mediatrack.append("Exposure time", str(tags["EXIF ExposureTime"]) + " sec.")

                        mediatrack.append("Flash fired", tags.get("EXIF Flash", None))
                        mediatrack.append("Metering mode", tags.get("EXIF MeteringMode", None))

                        exifmediatrack = MediaFileTrack("Image EXIF Data")

                        for tag in tags.keys():
                            if tag not in ("JPEGThumbnail",
                                           "TIFFThumbnail",
                                           "Filename",
                                           "EXIF MakerNote",
                                           "EXIF UserComment"
                                           ):
                                exifmediatrack.append(tag, tags[tag])

                        mediafile.tracks.append(exifmediatrack)

            if len(mediafile.tracks) == 0:
                continue

            actual_files.append(mediafile)

        if len(actual_files) == 0:
            return []

        self.property_label = Gtk.Label("Media")
        self.property_label.show()

        self.builder = Gtk.Builder()
        self.builder.add_from_string(GUI)
        self.treev: Gtk.TreeView = self.builder.get_object("treev")

        self.store = Gtk.TreeStore(str, str)
        self.treev.set_model(self.store)

        for i in actual_files:
            fileparent = None

            if len(actual_files) > 1:
                fileparent = self.store.append(None, [i.shortname, ""])

            for mt in i.tracks:
                storetrack: Gtk.TreeIter = self.store.append(fileparent, [mt.name, ""])

                for prop in mt.properties:
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

    def get_name_and_desc(self):

        return [("Nemo Media Tab:::View video/audio/image information from the properties tab in Nemo.")]
# ==============================================================================
