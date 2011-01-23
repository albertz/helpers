# -*- coding: utf-8 -*-

# simple exif reader
# code based on Python Imaging Library
# Advantage over PIL: It also reads broken EXIF.
# by Albert Zeyer

# TODO:
#  - be able to read JPEG (and maybe others) without PIL
#  - be able to safe EXIF (most functions should already be in place for that)


# The Python Imaging Library (PIL) is
#
#    Copyright © 1997-2011 by Secret Labs AB
#    Copyright © 1995-2011 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its associated documentation,
# you agree that you have read, understood, and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and its associated documentation
# for any purpose and without fee is hereby granted, provided that the above copyright notice appears
# in all copies, and that both that copyright notice and this permission notice appear in supporting
# documentation, and that the name of Secret Labs AB or the author not be used in advertising or
# publicity pertaining to distribution of the software without specific, written prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE
# LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
# ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import array, string, sys

II = "II" # little-endian (intel-style)
MM = "MM" # big-endian (motorola-style)

try:
    if sys.byteorder == "little":
        native_prefix = II
    else:
        native_prefix = MM
except AttributeError:
    if ord(array.array("i",[1]).tostring()[0]):
        native_prefix = II
    else:
        native_prefix = MM


DEBUG = False


SAFEBLOCK = 1024*1024

##
# Reads large blocks in a safe way.  Unlike fp.read(n), this function
# doesn't trust the user.  If the requested size is larger than
# SAFEBLOCK, the file is read block by block.
#
# @param fp File handle.  Must implement a <b>read</b> method.
# @param size Number of bytes to read.
# @return A string containing up to <i>size</i> bytes of data.

def _safe_read(fp, size):
    if size <= 0:
        return ""
    if size <= SAFEBLOCK:
        return fp.read(size)
    data = []
    while size > 0:
        block = fp.read(min(size, SAFEBLOCK))
        if not block:
            break
        data.append(block)
        size = size - len(block)
    return string.join(data, "")


#
# --------------------------------------------------------------------
# Read TIFF files

def il16(c,o=0):
    return ord(c[o]) + (ord(c[o+1])<<8)
def il32(c,o=0):
    return ord(c[o]) + (ord(c[o+1])<<8) + (ord(c[o+2])<<16) + (ord(c[o+3])<<24)
def ol16(i):
    return chr(i&255) + chr(i>>8&255)
def ol32(i):
    return chr(i&255) + chr(i>>8&255) + chr(i>>16&255) + chr(i>>24&255)

def ib16(c,o=0):
    return ord(c[o+1]) + (ord(c[o])<<8)
def ib32(c,o=0):
    return ord(c[o+3]) + (ord(c[o+2])<<8) + (ord(c[o+1])<<16) + (ord(c[o])<<24)
def ob16(i):
    return chr(i>>8&255) + chr(i&255)
def ob32(i):
    return chr(i>>24&255) + chr(i>>16&255) + chr(i>>8&255) + chr(i&255)



# a few tag names, just to make the code below a bit more readable
IMAGEWIDTH = 256
IMAGELENGTH = 257
BITSPERSAMPLE = 258
COMPRESSION = 259
PHOTOMETRIC_INTERPRETATION = 262
FILLORDER = 266
IMAGEDESCRIPTION = 270
STRIPOFFSETS = 273
SAMPLESPERPIXEL = 277
ROWSPERSTRIP = 278
STRIPBYTECOUNTS = 279
X_RESOLUTION = 282
Y_RESOLUTION = 283
PLANAR_CONFIGURATION = 284
RESOLUTION_UNIT = 296
SOFTWARE = 305
DATE_TIME = 306
ARTIST = 315
PREDICTOR = 317
COLORMAP = 320
TILEOFFSETS = 324
EXTRASAMPLES = 338
SAMPLEFORMAT = 339
JPEGTABLES = 347
COPYRIGHT = 33432
IPTC_NAA_CHUNK = 33723 # newsphoto properties
PHOTOSHOP_CHUNK = 34377 # photoshop properties
ICCPROFILE = 34675
EXIFIFD = 34665
XMP = 700

COMPRESSION_INFO = {
    # Compression => pil compression name
    1: "raw",
    2: "tiff_ccitt",
    3: "group3",
    4: "group4",
    5: "tiff_lzw",
    6: "tiff_jpeg", # obsolete
    7: "jpeg",
    32771: "tiff_raw_16", # 16-bit padding
    32773: "packbits"
}

OPEN_INFO = {
    # (ByteOrder, PhotoInterpretation, SampleFormat, FillOrder, BitsPerSample,
    #  ExtraSamples) => mode, rawmode
    (II, 0, 1, 1, (1,), ()): ("1", "1;I"),
    (II, 0, 1, 2, (1,), ()): ("1", "1;IR"),
    (II, 0, 1, 1, (8,), ()): ("L", "L;I"),
    (II, 0, 1, 2, (8,), ()): ("L", "L;IR"),
    (II, 1, 1, 1, (1,), ()): ("1", "1"),
    (II, 1, 1, 2, (1,), ()): ("1", "1;R"),
    (II, 1, 1, 1, (8,), ()): ("L", "L"),
    (II, 1, 1, 1, (8,8), (2,)): ("LA", "LA"),
    (II, 1, 1, 2, (8,), ()): ("L", "L;R"),
    (II, 1, 1, 1, (16,), ()): ("I;16", "I;16"),
    (II, 1, 2, 1, (16,), ()): ("I;16S", "I;16S"),
    (II, 1, 2, 1, (32,), ()): ("I", "I;32S"),
    (II, 1, 3, 1, (32,), ()): ("F", "F;32F"),
    (II, 2, 1, 1, (8,8,8), ()): ("RGB", "RGB"),
    (II, 2, 1, 2, (8,8,8), ()): ("RGB", "RGB;R"),
    (II, 2, 1, 1, (8,8,8,8), (0,)): ("RGBX", "RGBX"),
    (II, 2, 1, 1, (8,8,8,8), (1,)): ("RGBA", "RGBa"),
    (II, 2, 1, 1, (8,8,8,8), (2,)): ("RGBA", "RGBA"),
    (II, 2, 1, 1, (8,8,8,8), (999,)): ("RGBA", "RGBA"), # corel draw 10
    (II, 3, 1, 1, (1,), ()): ("P", "P;1"),
    (II, 3, 1, 2, (1,), ()): ("P", "P;1R"),
    (II, 3, 1, 1, (2,), ()): ("P", "P;2"),
    (II, 3, 1, 2, (2,), ()): ("P", "P;2R"),
    (II, 3, 1, 1, (4,), ()): ("P", "P;4"),
    (II, 3, 1, 2, (4,), ()): ("P", "P;4R"),
    (II, 3, 1, 1, (8,), ()): ("P", "P"),
    (II, 3, 1, 1, (8,8), (2,)): ("PA", "PA"),
    (II, 3, 1, 2, (8,), ()): ("P", "P;R"),
    (II, 5, 1, 1, (8,8,8,8), ()): ("CMYK", "CMYK"),
    (II, 6, 1, 1, (8,8,8), ()): ("YCbCr", "YCbCr"),
    (II, 8, 1, 1, (8,8,8), ()): ("LAB", "LAB"),

    (MM, 0, 1, 1, (1,), ()): ("1", "1;I"),
    (MM, 0, 1, 2, (1,), ()): ("1", "1;IR"),
    (MM, 0, 1, 1, (8,), ()): ("L", "L;I"),
    (MM, 0, 1, 2, (8,), ()): ("L", "L;IR"),
    (MM, 1, 1, 1, (1,), ()): ("1", "1"),
    (MM, 1, 1, 2, (1,), ()): ("1", "1;R"),
    (MM, 1, 1, 1, (8,), ()): ("L", "L"),
    (MM, 1, 1, 1, (8,8), (2,)): ("LA", "LA"),
    (MM, 1, 1, 2, (8,), ()): ("L", "L;R"),
    (MM, 1, 1, 1, (16,), ()): ("I;16B", "I;16B"),
    (MM, 1, 2, 1, (16,), ()): ("I;16BS", "I;16BS"),
    (MM, 1, 2, 1, (32,), ()): ("I;32BS", "I;32BS"),
    (MM, 1, 3, 1, (32,), ()): ("F;32BF", "F;32BF"),
    (MM, 2, 1, 1, (8,8,8), ()): ("RGB", "RGB"),
    (MM, 2, 1, 2, (8,8,8), ()): ("RGB", "RGB;R"),
    (MM, 2, 1, 1, (8,8,8,8), (0,)): ("RGBX", "RGBX"),
    (MM, 2, 1, 1, (8,8,8,8), (1,)): ("RGBA", "RGBa"),
    (MM, 2, 1, 1, (8,8,8,8), (2,)): ("RGBA", "RGBA"),
    (MM, 2, 1, 1, (8,8,8,8), (999,)): ("RGBA", "RGBA"), # corel draw 10
    (MM, 3, 1, 1, (1,), ()): ("P", "P;1"),
    (MM, 3, 1, 2, (1,), ()): ("P", "P;1R"),
    (MM, 3, 1, 1, (2,), ()): ("P", "P;2"),
    (MM, 3, 1, 2, (2,), ()): ("P", "P;2R"),
    (MM, 3, 1, 1, (4,), ()): ("P", "P;4"),
    (MM, 3, 1, 2, (4,), ()): ("P", "P;4R"),
    (MM, 3, 1, 1, (8,), ()): ("P", "P"),
    (MM, 3, 1, 1, (8,8), (2,)): ("PA", "PA"),
    (MM, 3, 1, 2, (8,), ()): ("P", "P;R"),
    (MM, 5, 1, 1, (8,8,8,8), ()): ("CMYK", "CMYK"),
    (MM, 6, 1, 1, (8,8,8), ()): ("YCbCr", "YCbCr"),
    (MM, 8, 1, 1, (8,8,8), ()): ("LAB", "LAB"),

}

PREFIXES = ["MM\000\052", "II\052\000", "II\xBC\000"]

def _accept(prefix):
    return prefix[:4] in PREFIXES



##
# Wrapper for TIFF IFDs.

class TiffImageFileDirectory:

    # represents a TIFF tag directory.  to speed things up,
    # we don't decode tags unless they're asked for.

    def __init__(self, prefix):
        self.prefix = prefix[:2]
        if self.prefix == MM:
            self.i16, self.i32 = ib16, ib32
            self.o16, self.o32 = ob16, ob32
        elif self.prefix == II:
            self.i16, self.i32 = il16, il32
            self.o16, self.o32 = ol16, ol32
        else:
            raise SyntaxError("not a TIFF IFD")
        self.reset()

    def reset(self):
        self.tags = {}
        self.tagdata = {}
        self.tagtype = {} # added 2008-06-05 by Florian Hoech
        self.next = None

    # dictionary API (sort of)

    def keys(self):
        return self.tagdata.keys() + self.tags.keys()

    def items(self):
        items = self.tags.items()
        for tag in self.tagdata.keys():
            items.append((tag, self[tag]))
        return items

    def __len__(self):
        return len(self.tagdata) + len(self.tags)

    def __getitem__(self, tag):
        try:
            return self.tags[tag]
        except KeyError:
            type, data = self.tagdata[tag] # unpack on the fly
            size, handler = self.load_dispatch[type]
            self.tags[tag] = data = handler(self, data)
            del self.tagdata[tag]
            return data

    def get(self, tag, default=None):
        try:
            return self[tag]
        except KeyError:
            return default

    def getscalar(self, tag, default=None):
        try:
            value = self[tag]
            if len(value) != 1:
                if tag == SAMPLEFORMAT:
                    # work around broken (?) matrox library
                    # (from Ted Wright, via Bob Klimek)
                    raise KeyError # use default
                raise ValueError, "not a scalar"
            return value[0]
        except KeyError:
            if default is None:
                raise
            return default

    def has_key(self, tag):
        return self.tags.has_key(tag) or self.tagdata.has_key(tag)

    def __setitem__(self, tag, value):
        if type(value) is not type(()):
            value = (value,)
        self.tags[tag] = value

    # load primitives

    load_dispatch = {}

    def load_byte(self, data):
        l = []
        for i in range(len(data)):
            l.append(ord(data[i]))
        return tuple(l)
    load_dispatch[1] = (1, load_byte)

    def load_string(self, data):
        if data[-1:] == '\0':
            data = data[:-1]
        return data
    load_dispatch[2] = (1, load_string)

    def load_short(self, data):
        l = []
        for i in range(0, len(data), 2):
            l.append(self.i16(data, i))
        return tuple(l)
    load_dispatch[3] = (2, load_short)

    def load_long(self, data):
        l = []
        for i in range(0, len(data), 4):
            l.append(self.i32(data, i))
        return tuple(l)
    load_dispatch[4] = (4, load_long)

    def load_rational(self, data):
        l = []
        for i in range(0, len(data), 8):
            l.append((self.i32(data, i), self.i32(data, i+4)))
        return tuple(l)
    load_dispatch[5] = (8, load_rational)

    def load_float(self, data):
        a = array.array("f", data)
        if self.prefix != native_prefix:
            a.byteswap()
        return tuple(a)
    load_dispatch[11] = (4, load_float)

    def load_double(self, data):
        a = array.array("d", data)
        if self.prefix != native_prefix:
            a.byteswap()
        return tuple(a)
    load_dispatch[12] = (8, load_double)

    def load_undefined(self, data):
        # Untyped data
        return data
    load_dispatch[7] = (1, load_undefined)

    def load(self, fp):
        # load tag dictionary

        self.reset()

        i16 = self.i16
        i32 = self.i32

        for i in range(i16(fp.read(2))):

            ifd = fp.read(12)

            tag, typ = i16(ifd), i16(ifd, 2)

            if DEBUG:
                import TiffTags
                tagname = TiffTags.TAGS.get(tag, "unknown")
                typname = TiffTags.TYPES.get(typ, "unknown")
                print "tag: %s (%d)" % (tagname, tag),
                print "- type: %s (%d)" % (typname, typ),

            try:
                dispatch = self.load_dispatch[typ]
            except KeyError:
                if DEBUG:
                    print "- unsupported type", typ
                continue # ignore unsupported type

            size, handler = dispatch

            size = size * i32(ifd, 4)

            # Get and expand tag value
            if size > 4:
                here = fp.tell()
                fp.seek(i32(ifd, 8))
                data = _safe_read(fp, size)
                fp.seek(here)
            else:
                data = ifd[8:8+size]

            if len(data) != size:
                #raise IOError, "not enough data"
                # don't raise an exception, just stop reading
                break
				
            self.tagdata[tag] = typ, data
            self.tagtype[tag] = typ

            if DEBUG:
                if tag in (COLORMAP, IPTC_NAA_CHUNK, PHOTOSHOP_CHUNK, ICCPROFILE, XMP):
                    print "- value: <table: %d bytes>" % size
                else:
                    print "- value:", self[tag]

        self.next = i32(fp.read(4))

    # save primitives

    def save(self, fp):

        o16 = self.o16
        o32 = self.o32

        fp.write(o16(len(self.tags)))

        # always write in ascending tag order
        tags = self.tags.items()
        tags.sort()

        directory = []
        append = directory.append

        offset = fp.tell() + len(self.tags) * 12 + 4

        stripoffsets = None

        # pass 1: convert tags to binary format
        for tag, value in tags:

            typ = None

            if self.tagtype.has_key(tag):
                typ = self.tagtype[tag]

            if typ == 1:
                # byte data
                data = value = string.join(map(chr, value), "")
            elif typ == 7:
                # untyped data
                data = value = string.join(value, "")
            elif type(value[0]) is type(""):
                # string data
                typ = 2
                data = value = string.join(value, "\0") + "\0"
            else:
                # integer data
                if tag == STRIPOFFSETS:
                    stripoffsets = len(directory)
                    typ = 4 # to avoid catch-22
                elif tag in (X_RESOLUTION, Y_RESOLUTION):
                    # identify rational data fields
                    typ = 5
                elif not typ:
                    typ = 3
                    for v in value:
                        if v >= 65536:
                            typ = 4
                if typ == 3:
                    data = string.join(map(o16, value), "")
                else:
                    data = string.join(map(o32, value), "")

            if DEBUG:
                import TiffTags
                tagname = TiffTags.TAGS.get(tag, "unknown")
                typname = TiffTags.TYPES.get(typ, "unknown")
                print "save: %s (%d)" % (tagname, tag),
                print "- type: %s (%d)" % (typname, typ),
                if tag in (COLORMAP, IPTC_NAA_CHUNK, PHOTOSHOP_CHUNK, ICCPROFILE, XMP):
                    size = len(data)
                    print "- value: <table: %d bytes>" % size
                else:
                    print "- value:", value

            # figure out if data fits into the directory
            if len(data) == 4:
                append((tag, typ, len(value), data, ""))
            elif len(data) < 4:
                append((tag, typ, len(value), data + (4-len(data))*"\0", ""))
            else:
                count = len(value)
                if typ == 5:
                    count = count / 2        # adjust for rational data field
                append((tag, typ, count, o32(offset), data))
                offset = offset + len(data)
                if offset & 1:
                    offset = offset + 1 # word padding

        # update strip offset data to point beyond auxiliary data
        if stripoffsets is not None:
            tag, typ, count, value, data = directory[stripoffsets]
            assert not data, "multistrip support not yet implemented"
            value = o32(self.i32(value) + offset)
            directory[stripoffsets] = tag, typ, count, value, data

        # pass 2: write directory to file
        for tag, typ, count, value, data in directory:
            if DEBUG > 1:
                print tag, typ, count, repr(value), repr(data)
            fp.write(o16(tag) + o16(typ) + o32(count) + value)

        # -- overwrite here for multi-page --
        fp.write("\0\0\0\0") # end of directory

        # pass 3: write auxiliary data to file
        for tag, typ, count, value, data in directory:
            fp.write(data)
            if len(data) & 1:
                fp.write("\0")

        return offset



##
# This module provides constants and clear-text names for various
# well-known EXIF tags.
##

##
# Maps EXIF tags to tag names.

TAGS = {

    # possibly incomplete
    0x0100: "ImageWidth",
    0x0101: "ImageLength",
    0x0102: "BitsPerSample",
    0x0103: "Compression",
    0x0106: "PhotometricInterpretation",
    0x010e: "ImageDescription",
    0x010f: "Make",
    0x0110: "Model",
    0x0111: "StripOffsets",
    0x0112: "Orientation",
    0x0115: "SamplesPerPixel",
    0x0116: "RowsPerStrip",
    0x0117: "StripByteConunts",
    0x011a: "XResolution",
    0x011a: "XResolution",
    0x011b: "YResolution",
    0x011b: "YResolution",
    0x011c: "PlanarConfiguration",
    0x0128: "ResolutionUnit",
    0x0128: "ResolutionUnit",
    0x012d: "TransferFunction",
    0x0131: "Software",
    0x0132: "DateTime",
    0x013b: "Artist",
    0x013e: "WhitePoint",
    0x013f: "PrimaryChromaticities",
    0x0201: "JpegIFOffset",
    0x0202: "JpegIFByteCount",
    0x0211: "YCbCrCoefficients",
    0x0211: "YCbCrCoefficients",
    0x0212: "YCbCrSubSampling",
    0x0213: "YCbCrPositioning",
    0x0213: "YCbCrPositioning",
    0x0214: "ReferenceBlackWhite",
    0x0214: "ReferenceBlackWhite",
    0x1000: "RelatedImageFileFormat",
    0x1001: "RelatedImageLength",
    0x1001: "RelatedImageWidth",
    0x828d: "CFARepeatPatternDim",
    0x828e: "CFAPattern",
    0x828f: "BatteryLevel",
    0x8298: "Copyright",
    0x829a: "ExposureTime",
    0x829d: "FNumber",
    0x8769: "ExifOffset",
    0x8773: "InterColorProfile",
    0x8822: "ExposureProgram",
    0x8824: "SpectralSensitivity",
    0x8825: "GPSInfo",
    0x8827: "ISOSpeedRatings",
    0x8828: "OECF",
    0x8829: "Interlace",
    0x882a: "TimeZoneOffset",
    0x882b: "SelfTimerMode",
    0x9000: "ExifVersion",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x9101: "ComponentsConfiguration",
    0x9102: "CompressedBitsPerPixel",
    0x9201: "ShutterSpeedValue",
    0x9202: "ApertureValue",
    0x9203: "BrightnessValue",
    0x9204: "ExposureBiasValue",
    0x9205: "MaxApertureValue",
    0x9206: "SubjectDistance",
    0x9207: "MeteringMode",
    0x9208: "LightSource",
    0x9209: "Flash",
    0x920a: "FocalLength",
    0x920b: "FlashEnergy",
    0x920c: "SpatialFrequencyResponse",
    0x920d: "Noise",
    0x9211: "ImageNumber",
    0x9212: "SecurityClassification",
    0x9213: "ImageHistory",
    0x9214: "SubjectLocation",
    0x9215: "ExposureIndex",
    0x9216: "TIFF/EPStandardID",
    0x927c: "MakerNote",
    0x9286: "UserComment",
    0x9290: "SubsecTime",
    0x9291: "SubsecTimeOriginal",
    0x9292: "SubsecTimeDigitized",
    0xa000: "FlashPixVersion",
    0xa001: "ColorSpace",
    0xa002: "ExifImageWidth",
    0xa003: "ExifImageHeight",
    0xa004: "RelatedSoundFile",
    0xa005: "ExifInteroperabilityOffset",
    0xa20b: "FlashEnergy",
    0xa20c: "SpatialFrequencyResponse",
    0xa20e: "FocalPlaneXResolution",
    0xa20f: "FocalPlaneYResolution",
    0xa210: "FocalPlaneResolutionUnit",
    0xa214: "SubjectLocation",
    0xa215: "ExposureIndex",
    0xa217: "SensingMethod",
    0xa300: "FileSource",
    0xa301: "SceneType",
    0xa302: "CFAPattern",

}

##
# Maps EXIF GSP tags to tag names.

GPSTAGS = {
    0: "GPSVersionID",
    1: "GPSLatitudeRef",
    2: "GPSLatitude",
    3: "GPSLongitudeRef",
    4: "GPSLongitude",
    5: "GPSAltitudeRef",
    6: "GPSAltitude",
    7: "GPSTimeStamp",
    8: "GPSSatellites",
    9: "GPSStatus",
    10: "GPSMeasureMode",
    11: "GPSDOP",
    12: "GPSSpeedRef",
    13: "GPSSpeed",
    14: "GPSTrackRef",
    15: "GPSTrack",
    16: "GPSImgDirectionRef",
    17: "GPSImgDirection",
    18: "GPSMapDatum",
    19: "GPSDestLatitudeRef",
    20: "GPSDestLatitude",
    21: "GPSDestLongitudeRef",
    22: "GPSDestLongitude",
    23: "GPSDestBearingRef",
    24: "GPSDestBearing",
    25: "GPSDestDistanceRef",
    26: "GPSDestDistance"
}


def getexif(im):
	# Extract EXIF information.  This method is highly experimental,
	# and is likely to be replaced with something better in a future
	# version.

	data = None

	import os
	if type(im) == str and os.path.isfile(im):
		import Image
		im = Image.open(im)
		
	try:
		# this works if im is an image loaded by PIL
		data = im.info["exif"]
	except KeyError:
		return {} # it meens there is no Exif entry
	except:
		try:
			# maybe this is the info-dict of an image loaded by PIL
			data = im["exif"]
		except KeyError:
			return {} # it meens there is no Exif entry
		except:
			# let's asume that im is Exif itself
			data = im

	if type(data) != str:
		raise Exception("expecting an image, an info-dict or Exif data")

	if data[0:6] != "Exif\x00\x00":
		raise Exception("no exif data: " + repr(data[0:6]))
		#return None # no exif-data

	import StringIO
	def fixup(value):
		if len(value) == 1:
			return value[0]
		return value

	# The EXIF record consists of a TIFF file embedded in a JPEG
	# application marker (!).

	file = StringIO.StringIO(data[6:])
	head = file.read(8)
	exif = {}
	
	# process dictionary
	info = TiffImageFileDirectory(head)
	info.load(file)
	for key, value in info.items():
		exif[key] = fixup(value)
	
	# get exif extension
	try:
		file.seek(exif[0x8769])
	except KeyError:
		pass
	else:
		info = TiffImageFileDirectory(head)
		info.load(file)
		for key, value in info.items():
			exif[key] = fixup(value)
	
	# get gpsinfo extension
	try:
		file.seek(exif[0x8825])
	except KeyError:
		pass
	else:
		info = TiffImageFileDirectory(head)
		info.load(file)
		exif[0x8825] = gps = {}
		for key, value in info.items():
			gps[key] = fixup(value)
			
	ret = {}
	for tag, value in exif.iteritems():
		decoded = TAGS.get(tag, tag)
		ret[decoded] = value
	return ret
