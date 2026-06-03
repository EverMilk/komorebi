"""Generate the README demo GIF — no browser, no screen capture.

This renders the *actual* Komorebi demo loop offline so the result is faithful
rather than mocked up:

* the reply text comes from the real ``EchoBackend`` (the zero-key demo brain),
* the per-sentence emotion comes from the real ``HeuristicClassifier``,
* the face is drawn with the exact geometry/palette of ``PlaceholderAvatar.js``.

So the GIF shows precisely what a first-time visitor sees at
``http://localhost:8000`` (and, in the live tail, at ``/?mode=live``) — just
deterministically composited into an animation instead of recorded.

Usage::

    python scripts/generate_demo_gif.py                 # -> docs/demo.gif
    python scripts/generate_demo_gif.py --no-live        # chat scene only
    python scripts/generate_demo_gif.py --fps 14 --width 360

Requires Pillow (a dev-only dependency; not needed to run Komorebi).
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "core"))

from komorebi.backends.llm.echo import EchoBackend  # noqa: E402
from komorebi.emotion import HeuristicClassifier  # noqa: E402
from komorebi.orchestrator import split_sentences  # noqa: E402
from komorebi.persona import load_persona  # noqa: E402

# --- palette + geometry, mirrored from PlaceholderAvatar.js / index.html ------

EMOTION_STYLE = {
    "neutral": {"face": (244, 217, 192), "brow": 0.0, "mouth": 0.0, "eye": 1.0},
    "joy": {"face": (255, 226, 192), "brow": 0.2, "mouth": 0.6, "eye": 0.8},
    "sadness": {"face": (230, 220, 208), "brow": -0.3, "mouth": -0.5, "eye": 0.7},
    "anger": {"face": (246, 201, 176), "brow": -0.5, "mouth": -0.3, "eye": 1.1},
    "surprise": {"face": (255, 230, 204), "brow": 0.5, "mouth": 0.0, "eye": 1.4},
    "fear": {"face": (233, 218, 208), "brow": 0.3, "mouth": -0.2, "eye": 1.3},
    "thinking": {"face": (239, 224, 205), "brow": 0.1, "mouth": 0.0, "eye": 0.9},
}
VISEME_OPEN = {"rest": 0.05, "a": 1.0, "i": 0.3, "u": 0.4, "e": 0.6, "o": 0.8}
_VOWELS = {"a": "aあ", "i": "iい", "u": "uう", "e": "eえ", "o": "oお"}

EYE_COLOR = (58, 44, 34)
BROW_COLOR = (90, 70, 54)
MOUTH_COLOR = (122, 59, 52)
TEXT_COLOR = (238, 243, 238)
ACCENT = (108, 193, 138)
LIVE_RED = (229, 115, 115)
BG_CENTER = (42, 59, 46)   # #2a3b2e
BG_EDGE = (20, 32, 26)     # #14201a
PANEL_LIGHTEN = 12         # rgba(255,255,255,0.04) over the gradient

STAGE = 320

# A CJK-capable font is required for the Japanese subtitles. Try the common
# Windows / macOS / Linux locations; let --font override.
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
_FONT_BOLD_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryob.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]


def _resolve_font(override: str | None, candidates: list[str]) -> str:
    for path in ([override] if override else []) + candidates:
        if path and Path(path).exists():
            return path
    raise SystemExit(
        "No CJK font found. Pass --font <path-to-a-Japanese-.ttc/.otf> "
        "(e.g. Noto Sans CJK)."
    )


def _vowel_open(ch: str) -> float:
    for vowel, members in _VOWELS.items():
        if ch in members or ch.lower() == vowel:
            return VISEME_OPEN[vowel]
    return 0.22  # consonant/kanji: a little movement so it reads as articulation


def _quad(p0, p1, p2, n=16):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def _background(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    cx, cy = w * 0.5, h * 0.2
    maxd = math.hypot(max(cx, w - cx), max(cy, h - cy))
    for y in range(h):
        for x in range(w):
            t = min(1.0, math.hypot(x - cx, y - cy) / maxd)
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(BG_CENTER, BG_EDGE))
    return img


def _draw_face(draw, cx, cy, style, k, mouth_open, blink):
    # Face
    draw.ellipse([cx - 110, cy - 130, cx + 110, cy + 130], fill=style["face"])
    # Eyes
    eye_y = cy - 20
    eye_dx = 45
    eye_r = 14 * style["eye"]
    for sign in (-1, 1):
        ex = cx + sign * eye_dx
        ry = max(1.0, eye_r * blink)
        draw.ellipse([ex - eye_r, eye_y - ry, ex + eye_r, eye_y + ry], fill=EYE_COLOR)
    # Brows
    brow_tilt = style["brow"] * k * 18
    for sign in (-1, 1):
        bx = cx + sign * eye_dx
        draw.line(
            [
                (bx - 18, eye_y - 28 + sign * brow_tilt),
                (bx + 18, eye_y - 28 - sign * brow_tilt),
            ],
            fill=BROW_COLOR,
            width=5,
        )
    # Mouth (two quadratic edges -> filled polygon)
    mouth_y = cy + 55
    open_h = 6 + mouth_open * 40
    curve = style["mouth"] * k * 22
    poly = _quad((cx - 35, mouth_y), (cx, mouth_y - curve), (cx + 35, mouth_y))
    poly += _quad((cx + 35, mouth_y), (cx, mouth_y + open_h + curve), (cx - 35, mouth_y))
    draw.polygon(poly, fill=MOUTH_COLOR)


def _wrap(draw, text, font, max_w):
    lines, line = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(line)
            line = ""
            continue
        if draw.textlength(line + ch, font=font) > max_w and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def _compose_frame(
    w, h, bg, fonts, *, style, k, mouth_open, blink, subtitle, live, chat_line
):
    img = bg.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    stage_x = (w - STAGE) // 2
    stage_y = 64
    # Stage panel (rgba white 0.04 over the gradient) + rounded corners.
    draw.rounded_rectangle(
        [stage_x, stage_y, stage_x + STAGE, stage_y + STAGE],
        radius=24,
        fill=(255, 255, 255, PANEL_LIGHTEN),
    )
    # Title
    title = "Komorebi"
    tw = draw.textlength(title, font=fonts["title"])
    leaf_x = (w - tw) / 2 - 26
    draw.ellipse([leaf_x, 22, leaf_x + 16, 38], fill=ACCENT)  # a little leaf
    draw.text(((w - tw) / 2, 18), title, font=fonts["title"], fill=(238, 243, 238, 220))
    if live:
        badge = "● LIVE"
        bw = draw.textlength(badge, font=fonts["small"])
        draw.text((w - bw - 18, 24), badge, font=fonts["small"], fill=LIVE_RED)
    # Face
    _draw_face(draw, w / 2, stage_y + STAGE / 2, style, k, mouth_open, blink)
    # Subtitle (character speech) — capped to 3 lines so it never clips.
    if subtitle:
        lines = _wrap(draw, subtitle, fonts["body"], STAGE - 8)
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:-1] + "…"
        sy = stage_y + STAGE + 16
        for ln in lines:
            lw = draw.textlength(ln, font=fonts["body"])
            draw.text(((w - lw) / 2, sy), ln, font=fonts["body"], fill=TEXT_COLOR)
            sy += 27
    # Live chat feed line
    if chat_line:
        who, _, msg = chat_line.partition(": ")
        cy = h - 30
        wlen = draw.textlength(who + "  ", font=fonts["small"])
        draw.text((stage_x, cy), who, font=fonts["small"], fill=ACCENT)
        draw.text((stage_x + wlen, cy), msg, font=fonts["small"], fill=(230, 235, 230))
    return img


async def _build_frames(width, fps, include_live, font_override=None):
    scale = width / float(_BASE_W)
    regular = _resolve_font(font_override, _FONT_CANDIDATES)
    bold = _resolve_font(font_override, _FONT_BOLD_CANDIDATES + _FONT_CANDIDATES)
    fonts = {
        "title": ImageFont.truetype(bold, 26),
        "body": ImageFont.truetype(regular, 19),
        "small": ImageFont.truetype(regular, 16),
    }
    bg = _background(_BASE_W, _BASE_H)
    clf = HeuristicClassifier(load_persona("komorebi").expression_bias)
    echo = EchoBackend()
    frames: list[Image.Image] = []

    def emit(n, **kw):
        for _ in range(n):
            frames.append(_compose_frame(_BASE_W, _BASE_H, bg, fonts, **kw))

    async def reply_for(prompt):
        chunks = [c async for c in echo.reply("", [{"role": "user", "content": prompt}])]
        return "".join(chunks).strip()

    async def speak(reply, *, live, chat_line):
        neutral = EMOTION_STYLE["neutral"]
        sentences = split_sentences(reply) or [reply]
        for sentence in sentences:
            cmd = await clf.classify(sentence)
            style = EMOTION_STYLE.get(cmd.emotion, neutral)
            for ch in (c for c in sentence if not c.isspace()):
                emit(
                    1,
                    style=style,
                    k=cmd.intensity,
                    mouth_open=_vowel_open(ch),
                    blink=1.0,
                    subtitle=reply,
                    live=live,
                    chat_line=chat_line,
                )
            # brief closed-mouth beat between sentences
            emit(
                2,
                style=style,
                k=cmd.intensity,
                mouth_open=0.05,
                blink=1.0,
                subtitle=reply,
                live=live,
                chat_line=chat_line,
            )

    # --- Scene 1: 1:1 chat (the zero-key demo) --------------------------------
    prompt = "おすすめの過ごし方は？"
    emit(int(fps * 0.7), style=EMOTION_STYLE["neutral"], k=0.2, mouth_open=0.05,
         blink=1.0, subtitle=prompt, live=False, chat_line=None)
    emit(2, style=EMOTION_STYLE["neutral"], k=0.2, mouth_open=0.05, blink=0.1,
         subtitle=prompt, live=False, chat_line=None)  # a blink
    reply = await reply_for(prompt)
    await speak(reply, live=False, chat_line=None)
    emit(int(fps * 0.8), style=EMOTION_STYLE["thinking"], k=0.4, mouth_open=0.05,
         blink=1.0, subtitle=reply, live=False, chat_line=None)

    # --- Scene 2: live broadcast tail (?mode=live) ----------------------------
    if include_live:
        chat = "そら: 今日のおすすめは？"
        emit(int(fps * 0.9), style=EMOTION_STYLE["neutral"], k=0.2, mouth_open=0.05,
             blink=1.0, subtitle="", live=True, chat_line=chat)
        live_reply = await reply_for("今日のおすすめは？")
        await speak(live_reply, live=True, chat_line=chat)
        emit(int(fps * 1.0), style=EMOTION_STYLE["joy"], k=0.6, mouth_open=0.05,
             blink=1.0, subtitle=live_reply, live=True, chat_line=chat)

    if scale != 1.0:
        size = (int(_BASE_W * scale), int(_BASE_H * scale))
        frames = [f.resize(size, Image.LANCZOS) for f in frames]
    return frames


_BASE_W, _BASE_H = 380, 524


def main() -> None:
    ap = argparse.ArgumentParser(description="Render the Komorebi demo GIF.")
    ap.add_argument("--output", default=str(_REPO / "docs" / "demo.gif"))
    ap.add_argument("--fps", type=int, default=14)
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--no-live", action="store_true", help="chat scene only")
    ap.add_argument("--font", default=None, help="path to a CJK font (.ttc/.otf)")
    args = ap.parse_args()

    frames = asyncio.run(
        _build_frames(args.width, args.fps, not args.no_live, args.font)
    )
    # Flat palette -> quantize without dither keeps edges crisp and size small.
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128, dither=Image.NONE) for f in frames]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pal[0].save(
        out,
        save_all=True,
        append_images=pal[1:],
        duration=int(1000 / args.fps),
        loop=0,
        optimize=True,
        disposal=2,
    )
    kb = out.stat().st_size / 1024
    print(f"wrote {out}  ({len(frames)} frames, {kb:.0f} KB)")


if __name__ == "__main__":
    main()
