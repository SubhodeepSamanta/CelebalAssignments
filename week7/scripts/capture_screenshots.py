"""
capture_screenshots.py
----------------------
Renders every tagged cell of the *executed* notebook into a PNG under screenshots/.

A cell is captured by adding a tag to its metadata:

    "tags": ["shot:03_scd1/03_merge_execution_metrics"]

The rendered image contains the real code and the real output that cell produced when
the notebook was executed - nothing is mocked or retyped.

Run (after executing the notebook):
    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import json
import keyword
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NOTEBOOK = os.path.join(ROOT, "notebooks", "delta_scd_assignment.ipynb")
SHOTS = os.path.join(ROOT, "screenshots")

# ---- look & feel ---------------------------------------------------------- #
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_UI = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_UI_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

FS = 14           # monospace font size
LH = 20           # line height
PAD = 18          # inner padding
MAX_COLS = 210    # widest line we will lay out
MAX_OUT_LINES = 110

BG = (255, 255, 255)
CHROME = (245, 246, 248)
BORDER = (214, 218, 224)
TITLE_BG = (33, 41, 54)
TITLE_FG = (240, 243, 247)
CODE_BG = (247, 247, 249)
PROMPT_IN = (48, 105, 176)
PROMPT_OUT = (186, 33, 33)
TXT = (32, 36, 44)
OUT_TXT = (42, 46, 54)
COMMENT = (94, 129, 84)
STRING = (176, 96, 44)
KEYWORD = (0, 90, 178)
NUMBER = (152, 66, 152)
BUILTIN = (0, 128, 128)

KW = set(keyword.kwlist) | {"self", "True", "False", "None"}
BUILTINS = {
    "print", "len", "int", "float", "str", "bool", "list", "dict", "set", "range",
    "sorted", "sum", "max", "min", "open", "zip", "enumerate", "map", "any", "all",
    "assert", "type", "round", "abs", "isinstance",
}

TOKEN_RE = re.compile(
    r"""(?P<comment>\#[^\n]*)
       |(?P<string>[rbfu]{0,2}(?:'''.*?'''|\"\"\".*?\"\"\"|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"))
       |(?P<number>\b\d+\.?\d*\b)
       |(?P<name>[A-Za-z_][A-Za-z0-9_]*)""",
    re.VERBOSE | re.DOTALL,
)


def load_fonts():
    return {
        "mono": ImageFont.truetype(FONT_MONO, FS),
        "mono_b": ImageFont.truetype(FONT_MONO_BOLD, FS),
        "ui": ImageFont.truetype(FONT_UI, 14),
        "ui_b": ImageFont.truetype(FONT_UI_BOLD, 15),
        "ui_s": ImageFont.truetype(FONT_UI, 12),
    }


def cell_output_text(cell) -> str:
    parts = []
    for out in cell.get("outputs", []):
        kind = out.get("output_type")
        if kind == "stream":
            parts.append("".join(out.get("text", [])))
        elif kind in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "text/plain" in data:
                parts.append("".join(data["text/plain"]))
        elif kind == "error":
            parts.append("\n".join(out.get("traceback", [])))
    text = "".join(parts)
    return re.sub(r"\x1b\[[0-9;]*m", "", text)  # strip ANSI colour codes


def colourise(line: str):
    """Split a code line into (text, colour) runs."""
    runs, pos = [], 0
    for m in TOKEN_RE.finditer(line):
        if m.start() > pos:
            runs.append((line[pos:m.start()], TXT))
        tok = m.group()
        if m.lastgroup == "comment":
            runs.append((tok, COMMENT))
        elif m.lastgroup == "string":
            runs.append((tok, STRING))
        elif m.lastgroup == "number":
            runs.append((tok, NUMBER))
        elif tok in KW:
            runs.append((tok, KEYWORD))
        elif tok in BUILTINS:
            runs.append((tok, BUILTIN))
        else:
            runs.append((tok, TXT))
        pos = m.end()
    if pos < len(line):
        runs.append((line[pos:], TXT))
    return runs


def wrap(lines, width):
    out = []
    for ln in lines:
        ln = ln.replace("\t", "    ").rstrip("\n")
        if len(ln) <= width:
            out.append(ln)
        else:
            indent = " " * (len(ln) - len(ln.lstrip()) + 2)
            out.append(ln[:width])
            rest = ln[width:]
            while rest:
                out.append(indent + rest[: width - len(indent)])
                rest = rest[width - len(indent):]
    return out


def render(title, subtitle, code_lines, out_lines, exec_count, path, fonts):
    char_w = fonts["mono"].getlength("M")
    code_lines = wrap(code_lines, MAX_COLS)
    out_lines = wrap(out_lines, MAX_COLS)

    truncated = 0
    if len(out_lines) > MAX_OUT_LINES:
        truncated = len(out_lines) - MAX_OUT_LINES
        out_lines = out_lines[:MAX_OUT_LINES]
        out_lines.append("")
        out_lines.append(f"... [{truncated} further output lines omitted from this screenshot]")

    gutter = int(char_w * 9)
    longest = max([len(l) for l in code_lines + out_lines] + [60])
    width = int(PAD * 2 + gutter + longest * char_w + PAD)
    width = max(width, 860)

    title_h = 52
    code_h = PAD + len(code_lines) * LH + PAD
    out_h = (PAD + len(out_lines) * LH + PAD) if out_lines else 0
    height = title_h + code_h + (8 + out_h if out_h else 0) + 14

    img = Image.new("RGB", (int(width), int(height)), BG)
    d = ImageDraw.Draw(img)

    # title bar
    d.rectangle([0, 0, width, title_h], fill=TITLE_BG)
    d.text((PAD, 9), title, font=fonts["ui_b"], fill=TITLE_FG)
    d.text((PAD, 30), subtitle, font=fonts["ui_s"], fill=(160, 172, 190))

    # code area
    y = title_h
    d.rectangle([0, y, width, y + code_h], fill=CODE_BG)
    d.line([0, y, width, y], fill=BORDER)
    d.line([gutter + PAD - 8, y, gutter + PAD - 8, y + code_h], fill=(226, 229, 234))
    ty = y + PAD
    d.text((PAD, ty), f"In [{exec_count}]:", font=fonts["mono_b"], fill=PROMPT_IN)
    for ln in code_lines:
        x = PAD + gutter
        for text, colour in colourise(ln):
            d.text((x, ty), text, font=fonts["mono"], fill=colour)
            x += fonts["mono"].getlength(text)
        ty += LH
    y += code_h
    d.line([0, y, width, y], fill=BORDER)

    # output area
    if out_lines:
        y += 8
        d.rectangle([0, y, width, y + out_h], fill=BG)
        ty = y + PAD
        d.text((PAD, ty), "Out:", font=fonts["mono_b"], fill=PROMPT_OUT)
        for ln in out_lines:
            d.text((PAD + gutter, ty), ln, font=fonts["mono"], fill=OUT_TXT)
            ty += LH
        y += out_h

    d.rectangle([0, 0, width - 1, height - 1], outline=BORDER)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return os.path.relpath(path, ROOT), img.size


def main():
    if not os.path.exists(NOTEBOOK):
        sys.exit(f"notebook not found: {NOTEBOOK}")

    nb = json.load(open(NOTEBOOK))
    fonts = load_fonts()

    executed = any(c.get("outputs") for c in nb["cells"] if c["cell_type"] == "code")
    if not executed:
        sys.exit("The notebook has no outputs - execute it before capturing screenshots.")

    made = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        tags = cell.get("metadata", {}).get("tags", [])
        shot = next((t.split("shot:", 1)[1] for t in tags if t.startswith("shot:")), None)
        if not shot:
            continue

        folder, name = shot.split("/", 1)
        pretty = name.split("_", 1)[1].replace("_", " ").title()
        section = folder.split("_", 1)[1].replace("_", " ").title()

        code = [l.rstrip("\n") for l in cell["source"]]
        out = cell_output_text(cell).split("\n")
        while out and not out[-1].strip():
            out.pop()

        path = os.path.join(SHOTS, folder, f"{name}.png")
        rel, size = render(
            title=f"{section} — {pretty}",
            subtitle="Assignment 7 · Delta Lake MERGE · notebooks/delta_scd_assignment.ipynb",
            code_lines=code,
            out_lines=out,
            exec_count=cell.get("execution_count") or " ",
            path=path,
            fonts=fonts,
        )
        made.append((rel, size))
        print(f"  {rel:<62} {size[0]}x{size[1]}")

    print(f"\n{len(made)} screenshots written under screenshots/")

    # index file so the folder is self-describing on GitHub
    index = ["# Screenshots", "",
             "Each image is a render of a cell from the executed notebook -",
             "the code shown and the output below it are exactly what ran.", ""]
    current = None
    for rel, _ in sorted(made):
        folder = rel.split(os.sep)[1]
        if folder != current:
            current = folder
            index.append(f"\n## {folder.split('_', 1)[1].replace('_', ' ').title()}\n")
        fname = os.path.basename(rel)
        index.append(f"- `{fname}` — {fname.split('_', 1)[1][:-4].replace('_', ' ')}")
    index.append("\n- `06_final_output/04_summary_charts.png` — matplotlib summary figure "
                 "(saved directly by the notebook)\n")
    with open(os.path.join(SHOTS, "README.md"), "w") as f:
        f.write("\n".join(index))


if __name__ == "__main__":
    main()
