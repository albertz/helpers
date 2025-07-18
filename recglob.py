# recursive glob
# by Albert Zeyer
# code under zlib

import os
import glob
import fnmatchex


def recglob(filepattern: str, *, followlinks: bool = False):
    """
    This function iterates ``dirname(filepattern) + "/**/" + basename(filepattern)``,
    where ``filepattern`` is matched via :func:`fnmatchex`.

    :param filepattern: "{dir}/{pattern}". :func:`fnmatchex` is used for ``pattern``
        (that is how it is different from :func:`glob`).
        Pattern expressions only supported for the basename yet.
    :param followlinks: if True, follow symbolic links to directories.
    :return: yields matching file names
    """

    dir = os.path.dirname(filepattern)
    pattern = os.path.basename(filepattern)

    # use iglob instead of listdir to get a lazy list
    for f in glob.iglob(dir + "/*"):
        if not followlinks and os.path.islink(f) and os.path.isdir(f):
            continue
        if os.path.isdir(f):
            for x in recglob(f + "/" + pattern, followlinks=followlinks):
                yield x
        else:
            if fnmatchex.fnmatchex(os.path.basename(f), pattern):
                yield f
