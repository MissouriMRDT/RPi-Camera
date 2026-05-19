#!/bin/python3

# v4l2-ctl -d <video device> --list-formats-ext > ./parse_video_formats.py
import re
import sys


def make_cs_dict(indent: str, values: dict[str]):
    if len(values) == 0:
        return "new() { }"
    return f"""new()
{indent}{{
{indent}    {f",\n{indent}    ".join([f'["{k}"] = {v}' for k, v in values.items()])}
{indent}}}"""


format_map = {"MJPG": "mjpeg", "YUYV": "yuyv422"}

input_ = sys.stdin.read()
output = {}

formats = re.findall(r": '(\w+)'", input_)
if len(formats) == 0:
    exit(0)
format_sections = re.split(r": '\w+'", input_)[1:]

for format_, format_section in zip(formats, format_sections):
    format_ = format_map[format_] if format_ in format_map else format_
    output[format_] = {}
    sizes = re.findall(r"\d+x\d+", format_section)
    size_sections = re.split(r"\d+x\d+", format_section)[1:]
    for size, size_section in zip(sizes, size_sections):
        if size not in output[format_]:
            output[format_][size] = []
        output[format_][size].extend(
            [int(float(x)) for x in re.findall(r"(\d+.?\d*) fps", size_section)]
        )
    for size in output[format_]:
        output[format_][size] = sorted(list(set(output[format_][size])))

print(
    make_cs_dict(
        "",
        {
            format_: make_cs_dict(
                "    ",
                {
                    size: f"[{', '.join([str(x) for x in fps])}]"
                    for size, fps in sizes.items()
                },
            )
            for format_, sizes in output.items()
        },
    )
)
