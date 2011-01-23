# -*- coding: utf-8 -*-

# simple exif reader
# code based on Python Imaging Library
# by Albert Zeyer

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


II = "II" # little-endian (intel-style)
MM = "MM" # big-endian (motorola-style)

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
                raise IOError, "not enough data"

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
		return None # it meens there is no Exif entry
	except:
		try:
			# maybe this is the info-dict of an image loaded by PIL
			data = im["exif"]
		except KeyError:
			return None # it meens there is no Exif entry
		except:
			# let's asume that im is Exif itself
			data = im

	if type(data) != str:
		raise Exception("expecting an image, an info-dict or Exif data")

	if data[0:6] != "Exif\x00\x00":
		return None # no exif-data

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
			
	from ExifTags import TAGS
	ret = {}
	for tag, value in exif.iteritems():
		try:
			decoded = TAGS.get(tag, tag)
			ret[decoded] = value
		except:
			pass
	return ret
