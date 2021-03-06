#!/usr/bin/env python3

# Simple pic/mov renamer script.
# by Albert Zeyer
# code under zlib


import argparse
from recglob import *
from cleanupstr import *
from pprint import pprint
import exif
import sys, os, time
from subprocess import check_call
import better_exchook
better_exchook.install()


def cleanup_exif_tags(exif):
    ret = {}
    for tag, value in exif.items():
        if type(tag) is int: continue
        if tag == "MakerNote": continue
        if isinstance(value, (str, bytes)):
            value = cleanupstr(value).strip()
        ret[tag] = value
    return ret


def file_time_creation(f):
    import os, time
    stats = os.stat(f)
    try:
        t = stats.st_birthtime
    except Exception:
        t = stats.st_ctime
    return time.strftime("%Y:%m:%d %H:%M:%S", time.localtime(t))


def iminfo(f):
    try:
        info = cleanup_exif_tags(exif.getexif(f))
    except exif.ExifException:
        info = {}
    if "DateTimeOriginal" in info:
        info["DateTime"] = info["DateTimeOriginal"]
    if "DateTime" not in info:
        info["DateTime"] = file_time_creation(f)
    return info


def user_input(text, convfunc):
    while True:
        try:
            s = input(text)
            return convfunc(s)
        except Exception as e:
            print("Error:", e)


def str_to_bool(s):
    if s.lower() in ["y", "yes", "ja", "j", "1"]: return True
    if s.lower() in ["n", "no", "nein", "0"]: return False
    raise Exception("I don't understand %r; please give me an Y or N" % s)


files = {}
files_utime = {}
errors = {}


def get_prefix_for_file(f, args):
    """

    Args:
        f (str):

    Returns:
        (str, str):
    """
    info = iminfo(f)
    date_time_str = info["DateTime"].replace(":", "_").replace(" ", "_")
    # prefix, eg. "2011_01_22", and time
    return date_time_str[:10], date_time_str[11:19]


def maybe_remove(s, content):
    """
    Args:
        s (str):
        content (str):

    Returns:
        str:
    """
    s = s.replace("_" + content + "_", "")
    s = s.replace("_" + content, "")
    s = s.replace(content + "_", "")
    s = s.replace(content, "")
    return s


def user_repr(v):
    if isinstance(v, str):
        if len(v) > 30: return repr(v[:30]) + "..."
        return repr(v)
    return repr(v)


def dump_exif(f):
    print("File", f, ":")
    try:
        info = exif.getexif(f)
    except exif.ExifException as e:
        print("  Error:", e)
    else:
        for k in sorted([k for k in info if isinstance(k, str)]) + sorted([k for k in info if not isinstance(k, str)]):
            print(" ", k, ":", user_repr(info[k]))
    print("  file creation time:", file_time_creation(f))


def file_ctime_underscore(f):
    return file_time_creation(f).replace(":", "_")


def file_mtime_underscore(f):
    t = os.stat(f).st_mtime
    return time.strftime("%Y_%m_%d %H_%M_%S", time.localtime(t))


def collect_file(f, args):
    if args.show_exif_only:
        dump_exif(f)
        return
    global files, files_utime, errors
    try:
        assert os.path.isfile(f), "is not a file: %s" % f
        date_prefix, time_prefix = get_prefix_for_file(f, args)
        if args.utime:
            if args.mtime:
                file_ctime = file_mtime_underscore(f)
            else:
                file_ctime = file_ctime_underscore(f)
            if date_prefix + " " + time_prefix != file_ctime:
                files_utime[f] = (file_ctime, date_prefix + " " + time_prefix)
        base_prefix = date_prefix
        if args.add_time:
            base_prefix += "_" + time_prefix
        prefix = base_prefix
        if args.add_prefix:
            prefix += "_" + args.add_prefix
        postfix = ""
        if args.add_postfix:
            postfix += "_" + args.add_postfix
        basename, ext = os.path.splitext(os.path.basename(f))
        basename = maybe_remove(basename, date_prefix)
        basename = maybe_remove(basename, date_prefix.replace("_", ""))
        if args.add_time:
            basename = maybe_remove(basename, time_prefix)
            basename = maybe_remove(basename, time_prefix.replace("_", ""))
        dirname = os.path.dirname(f) or "."
        newfn = dirname + "/" + prefix + "__" + basename + postfix + ext
        if os.path.exists(newfn):
            errors[f] = os.path.basename(newfn) + " already exists"
        elif os.path.basename(f)[:len(base_prefix)] == base_prefix:
            if not args.ignore_prefixed:
                errors[f] = os.path.basename(f) + " already has the prefix '" + base_prefix + "'"
        else:
            files[f] = newfn
    except exif.ExifException as e:
        errors[f] = str(e)


def collect_dir(dir, args):
    for f in recglob(dir + "/*.{jpeg,jpg,JPG,mov,MOV,png,PNG}"):
        collect_file(f, args)


def change_ctime(f, new_time):
    """
    Args:
        f (str):
        new_time (str): like "2017_09_05 13_23_49"

    Returns:
        Nothing.
    """
    ttup = time.strptime(new_time, "%Y_%m_%d %H_%M_%S")
    if sys.platform == "darwin":
        # SetFile format: "mm/dd/[yy]yy [hh:mm:[:ss] [AM | PM]]"
        tstr = time.strftime("%m/%d/%Y %H:%M:%S", ttup)
        args = ["SetFile", "-d", tstr, f]
        print("call:", args)
        check_call(args)
    tsecs = time.mktime(ttup)
    os.utime(f, (tsecs, tsecs))


def collect(fn, args):
    if os.path.isdir(fn):
        return collect_dir(fn, args)
    if os.path.isfile(fn):
        return collect_file(fn, args)
    raise Exception("no file or dir: %s" % fn)


def user_loop(args):
    while True:
        if len(errors) > 0:
            print("Errors (i.e. excluded files):")
            for f, err in sorted(errors.items()):
                print("", f, ":", err)
            print("")

        if len(files) > 0:
            print("Renames:")
            for old, new in sorted(files.items()):
                print("", old, "->", os.path.basename(new))
            print("")

        if len(files_utime) > 0:
            print("Change times:")
            for f, (old, new) in sorted(files_utime.items()):
                print("", f, ":", old, "->", new)
            print("")

        if len(files) == 0 and len(files_utime) == 0:
            if args.utime:
                print("No files to rename or touch. Quitting.")
            else:
                print("No files to rename. Quitting.")
            quit()

        if args.no_action:
            print("No action (--no_action). Quitting.")
            quit()

        ok = user_input("Confirm? (Y/N) ", str_to_bool)
        if ok:
            if len(files) > 0:
                for old, new in sorted(files.items()):
                    os.rename(old, new)
                print("All renames successfull.")
            if len(files_utime) > 0:
                for f, (old, new) in sorted(files_utime.items()):
                    change_ctime(f, new)
            quit()
        else:
            print("Abborting.")
            quit()


def main():
    argparser = argparse.ArgumentParser(
        description="""
        Renames pictures according to a pattern via EXIF.
        Adds a date (eg. "2011_01_22__") as a prefix to each file.
        Asks for confirmation, so it is safe to just try out and see what it would do.
        """
    )
    argparser.add_argument(
        'dirs_or_files', nargs="+",
        help="dirs/files to proceed")
    argparser.add_argument(
        '--add_time', action="store_true",
        help="add time to filename")
    argparser.add_argument(
        '--add_prefix', type=str,
        help="additional prefix to add")
    argparser.add_argument(
        '--add_postfix', type=str,
        help="additional postfix to add")
    argparser.add_argument(
        '--show_exif_only', action="store_true",
        help="show EXIF only and don't do anything")
    argparser.add_argument(
        '--ignore_prefixed', action="store_true",
        help="don't rename already prefixed files")
    argparser.add_argument(
        "--utime", action="store_true", help="change ctime/mtime")
    argparser.add_argument(
        "--mtime", action="store_true", help="look at mtime")
    argparser.add_argument(
        '--no_action', action="store_true",
        help="just try, don't do anything")
    args = argparser.parse_args()

    for fn in args.dirs_or_files:
        collect(fn, args)

    user_loop(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt. Abborting.")
        quit()
