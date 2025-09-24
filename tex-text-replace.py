#!/usr/bin/env python3

"""
A simple script to do regex-based text replacements in LaTeX files.

We specifically only want to do replacements in the text parts of the LaTeX files,
not in special commands (e.g. `\\label`, `\\cite`, etc.).
We have an allowed whitelist of LaTeX commands where replacements are allowed (e.g. `\\caption`).

Currently, this script only supports inplace editing of files.
"""

import argparse
import re


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-i", "--inplace", action="store_true", help="Edit files in place")
    arg_parser.add_argument("-p", "--pattern", type=str, required=True, help="Regex pattern to replace")
    arg_parser.add_argument("-r", "--replacement", type=str, required=True, help="Replacement string")
    arg_parser.add_argument("files", nargs="+", help="Files to process")
    args = arg_parser.parse_args()

    assert args.inplace, "Currently only inplace editing is supported."

    for file_path in args.files:
        with open(file_path, "r") as f:
            content = f.read()
        content = replace(content, args.pattern, args.replacement)
        with open(file_path, "w") as f:
            f.write(content)


def replace(text: str, pattern: str, replacement: str) -> str:
    # Allowed LaTeX commands where replacements are allowed
    allowed_commands = {
        "textbf",
        "textit",
        "emph",
        "caption",
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "subparagraph",
        "item",
        "itemize",
        "enumerate",
        "description",
        "title",
        "author",
        "date",
    }

    # Regex to match LaTeX commands or comments
    # Group 1: command, Group 8: comment
    token_regex = re.compile(
        r"(\\([a-zA-Z]+)\b(\[[^]]*\])?(\s*\{([^{}]*)\})?)"  # Command
        r"|((?<!\\)%.*)"  # Comment
    )

    # Split the text into parts: text, LaTeX commands, and comments
    parts = []
    last_end = 0
    for match in token_regex.finditer(text):
        start, end = match.span()
        if last_end < start:
            parts.append(("text", None, text[last_end:start]))
        if match.group(1):  # Command
            parts.append(("command", match, text[start:end]))
        elif match.group(6):  # Comment
            parts.append(("comment", match, text[start:end]))
        else:
            raise ValueError("Unexpected match in regex.")
        last_end = end
    if last_end < len(text):
        parts.append(("text", None, text[last_end:]))

    # Process each part
    new_parts = []
    for part_type, match_obj, part_text in parts:
        if part_type == "text":
            new_part_text = re.sub(pattern, replacement, part_text)
            new_parts.append(new_part_text)
        elif part_type == "command" and match_obj.group(2) in allowed_commands and match_obj.group(4):
            command_name = match_obj.group(2)
            optional_arg = match_obj.group(3) or ""
            arg = match_obj.group(5)
            new_arg = re.sub(pattern, replacement, arg)
            # group(4) contains the whitespace and braces
            new_command = f"\\{command_name}{optional_arg}{{{new_arg}}}"
            new_parts.append(new_command)
        else:
            new_parts.append(part_text)

    return "".join(new_parts)


if __name__ == "__main__":
    main()
