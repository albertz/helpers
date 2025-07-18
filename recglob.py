# recursive glob
# by Albert Zeyer
# code under zlib

import os
import glob


def recglob(filepattern: str):
    """
    usage: filepattern = dir + "/" + pattern
    filepattern: fnmatchex expr only supported for the basename yet
    this function iterates: dir + "/**/" + pattern
    """

    dir = os.path.dirname(filepattern)
    pattern = os.path.basename(filepattern)

    # Since Python 3.5, the original global supports recursive globs using “**”.
    return glob.glob(dir + "/**/" + pattern, recursive=True)
