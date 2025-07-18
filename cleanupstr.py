# string cleanup functions
# by Albert Zeyer
# code under zlib

from typing import Union


def cleanupstr(s: Union[str, bytes]) -> str:
    if isinstance(s, str):
        s = s.encode("utf8")
    assert isinstance(s, bytes)
    ret = ""
    for c in s:
        if c < 32:
            continue
        ret += chr(c)
    return ret
