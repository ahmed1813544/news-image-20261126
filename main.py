#!/usr/bin/env python3
"""THE WORLD TODAY -- Thursday 26 November 2026, in one image.

A code-drawn newspaper front page summing up the world's news of
Thursday 26 November 2026. Standard library only: a hand-rolled 5x7
bitmap font, a small rasterizer and a PNG encoder. No network, no
randomness, no time dependence -- the same bytes every run.

Writes to $MAKEFUN_OUTPUT_DIR/entry.png, or /output/entry.png.
Image: 1024 x 1024 PNG, well under 1 MiB.
"""

import os
import struct
import zlib
from binascii import crc32

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows; each row is a 5-bit integer,
# bit 4 = leftmost pixel. Lowercase letters sit on the same 7-row grid
# with a 2-row cap gap and descenders kept inside the grid.

FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 21, 10),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "a": (0, 0, 14, 1, 15, 17, 15),
    "b": (16, 16, 30, 17, 17, 17, 30),
    "c": (0, 0, 14, 17, 16, 17, 14),
    "d": (1, 1, 15, 17, 17, 17, 15),
    "e": (0, 0, 14, 17, 31, 16, 14),
    "f": (6, 9, 8, 30, 8, 8, 8),
    "g": (0, 15, 17, 17, 15, 1, 14),
    "h": (16, 16, 30, 17, 17, 17, 17),
    "i": (4, 0, 12, 4, 4, 4, 14),
    "j": (2, 0, 6, 2, 2, 2, 12),
    "k": (16, 16, 18, 20, 24, 20, 18),
    "l": (12, 4, 4, 4, 4, 4, 14),
    "m": (0, 0, 26, 21, 21, 21, 21),
    "n": (0, 0, 30, 17, 17, 17, 17),
    "o": (0, 0, 14, 17, 17, 17, 14),
    "p": (0, 0, 30, 17, 17, 30, 16),
    "q": (0, 0, 15, 17, 17, 15, 1),
    "r": (0, 0, 22, 25, 16, 16, 16),
    "s": (0, 0, 15, 16, 14, 1, 30),
    "t": (8, 8, 30, 8, 8, 8, 6),
    "u": (0, 0, 17, 17, 17, 19, 13),
    "v": (0, 0, 17, 17, 17, 10, 4),
    "w": (0, 0, 17, 21, 21, 21, 10),
    "x": (0, 0, 17, 10, 4, 10, 17),
    "y": (0, 0, 17, 17, 15, 1, 14),
    "z": (0, 0, 31, 2, 4, 8, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    "-": (0, 0, 0, 31, 0, 0, 0),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "%": (25, 26, 2, 4, 8, 19, 19),
    "$": (4, 15, 20, 14, 5, 30, 4),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "+": (0, 4, 4, 31, 4, 4, 0),
    "=": (0, 0, 31, 0, 31, 0, 0),
    "*": (0, 21, 14, 21, 0, 0, 0),
    "#": (10, 10, 31, 10, 31, 10, 10),
    "[": (14, 8, 8, 8, 8, 8, 14),
    "]": (14, 2, 2, 2, 2, 2, 14),
    "_": (0, 0, 0, 0, 0, 0, 31),
    "<": (2, 4, 8, 16, 8, 4, 2),
    ">": (8, 4, 2, 1, 2, 4, 8),
    "|": (4, 4, 4, 4, 4, 4, 4),
    "\\": (16, 8, 8, 4, 2, 2, 1),
    "~": (0, 0, 0, 10, 21, 0, 0),
    "\u2014": (0, 0, 0, 31, 0, 0, 0),   # em dash
    "\u2013": (0, 0, 0, 31, 0, 0, 0),   # en dash
    "\u2019": (4, 4, 8, 0, 0, 0, 0),    # right single quote
    "\u201c": (10, 10, 0, 0, 0, 0, 0),  # left double quote
    "\u201d": (10, 10, 0, 0, 0, 0, 0),  # right double quote
    "\u2022": (0, 0, 0, 12, 12, 0, 0),  # bullet
    "\u00b0": (12, 18, 18, 12, 0, 0, 0),  # degree
    "\u00a3": (6, 8, 8, 30, 8, 8, 30),  # pound
}

_UNKNOWN = FONT["?"]


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per char)."""
    return len(text) * 6 * scale


def wrap_text(text, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:(x1 - x0) * 3 + i] = c * (x1 - x0)

    def hline(self, x0, x1, y, c):
        if x0 > x1:
            x0, x1 = x1, x0
        self.rect(x0, y, x1 - x0 + 1, 1, c)

    def vline(self, x, y0, y1, c):
        if y0 > y1:
            y0, y1 = y1, y0
        self.rect(x, y0, 1, y1 - y0 + 1, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        """Filled circle."""
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r >= dy * dy else 0
            self.hline(cx - dx, cx + dx, yy, c)

    def ring(self, cx, cy, r, c):
        """Circle outline, 2 px thick."""
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if abs(d - r) <= 1.0:
                    self.px(xx, yy, c)

    def poly(self, pts, c):
        """Filled polygon (scanline fill)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(min(ys), 0), min(max(ys), self.h - 1) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, c)

    def text(self, x, y, s, scale, c, align="l"):
        """Draw text; y is the top of the 7-row glyph cell."""
        if align == "c":
            x -= text_width(s, scale) // 2
        elif align == "r":
            x -= text_width(s, scale)
        for ch in s:
            glyph = FONT.get(ch, _UNKNOWN)
            for row in range(7):
                bits = glyph[row]
                if not bits:
                    continue
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(x + col * scale, y + row * scale,
                                  scale, scale, c)
            x += 6 * scale

    def text_block(self, x, y, lines, scale, c, leading=None, align="l"):
        """Draw a list of lines; returns y just below the last line."""
        lh = leading if leading is not None else 7 * scale + 2
        for ln in lines:
            self.text(x, y, ln, scale, c, align=align)
            y += lh
        return y


# ---------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- palette
PAPER = bytes((246, 241, 227))
INK = bytes((20, 20, 20))
RED = bytes((176, 32, 32))
BLUE = bytes((29, 78, 137))
GOLD = bytes((176, 138, 44))
GREY = bytes((90, 86, 76))
LIGHT = bytes((232, 226, 208))
WHITE = bytes((255, 255, 255))
BLACK = bytes((0, 0, 0))
NAVY = bytes((18, 28, 52))
DUSK = bytes((232, 163, 76))
SEA = bytes((16, 42, 68))
ORANGE = bytes((232, 110, 30))
YELLOW = bytes((250, 200, 60))
GREEN = bytes((34, 120, 70))
TEAL = bytes((16, 110, 110))
PURPLE = bytes((96, 60, 140))

MARGIN = 12
CONTENT_W = W - 2 * MARGIN  # 1000


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- hero art
def draw_hero(cv, x, y, w, h):
    """Dusk over Riyadh: skyline, interceptor trails, a burning tanker
    in the Strait of Hormuz below. All fixed coordinates: deterministic."""
    # sky gradient, dusk bands
    top = (22, 34, 66)
    mid = (120, 70, 90)
    hor = (232, 163, 76)
    sky_h = h - 78
    for yy in range(sky_h):
        t = yy / max(sky_h - 1, 1)
        if t < 0.55:
            c = lerp(top, mid, t / 0.55)
        else:
            c = lerp(mid, hor, (t - 0.55) / 0.45)
        cv.rect(x, y + yy, w, 1, bytes(c))
    # stars
    for sx, sy in ((30, 18), (90, 40), (150, 14), (210, 34), (300, 22),
                   (380, 44), (470, 16), (540, 38), (60, 66), (250, 60),
                   (420, 70), (520, 62)):
        cv.px(x + sx, y + sy, WHITE)
        cv.px(x + sx + 1, y + sy, WHITE)
    # low moon
    cv.circle(x + w - 70, y + 52, 22, bytes((248, 240, 210)))
    cv.circle(x + w - 78, y + 46, 5, bytes((228, 218, 180)))
    cv.circle(x + w - 62, y + 60, 4, bytes((228, 218, 180)))
    # missile trails: two rising arcs with bright heads
    def trail(x0, y0, x1, y1, steps=26):
        for i in range(steps + 1):
            t = i / steps
            px = int(x0 + (x1 - x0) * t)
            py = int(y0 + (y1 - y0) * t - 70 * t * (1 - t) * 4)
            r = 3 if i > steps - 4 else 2
            cv.circle(x + px, y + py, r,
                      YELLOW if i > steps - 4 else bytes((250, 220, 140)))
    trail(90, sky_h - 6, 250, 60)
    trail(430, sky_h - 6, 300, 44)
    # interception burst
    bx, by = x + 300, y + 44
    cv.circle(bx, by, 16, ORANGE)
    cv.circle(bx, by, 10, YELLOW)
    cv.circle(bx, by, 5, WHITE)
    for dx, dy in ((-26, -8), (26, -10), (-20, 12), (24, 10), (0, -24),
                   (-8, 22)):
        cv.line(bx, by, bx + dx, by + dy, YELLOW)
    # second burst, smaller
    bx2, by2 = x + 250, y + 60
    cv.circle(bx2, by2, 9, ORANGE)
    cv.circle(bx2, by2, 4, YELLOW)
    # skyline silhouette
    base = y + sky_h
    buildings = [
        (0, 150, 46, 90), (46, 120, 40, 120), (86, 170, 54, 70),
        (140, 100, 44, 140), (184, 150, 40, 90), (224, 80, 46, 160),
        (270, 130, 42, 110), (312, 170, 48, 70), (360, 110, 44, 130),
        (404, 150, 40, 90), (444, 90, 46, 150), (490, 140, 44, 100),
        (534, 170, 40, 70), (574, 120, 26, 120),
    ]
    for bx0, top_y, bw, bh in buildings:
        cv.rect(x + bx0, base - bh, bw, bh, bytes((16, 20, 38)))
    # KAFD-style twisted tower
    cv.poly([(x + 232, base - 160), (x + 258, base - 160),
             (x + 252, base - 210), (x + 238, base - 210)], bytes((16, 20, 38)))
    cv.rect(x + 238, base - 226, 14, 18, bytes((16, 20, 38)))
    # lit windows, fixed pattern
    for wx in range(8, w - 8, 16):
        for wy in range(base - 150, base - 8, 22):
            if (wx * 7 + wy * 3) % 11 < 4:
                cv.rect(x + wx, wy, 3, 4, bytes((250, 200, 90)))
    # sea
    cv.rect(x, base, w, 78, SEA)
    for wy in range(base + 10, base + 74, 14):
        for wx in range(0, w, 46):
            off = (wy // 14) % 2 * 23
            cv.hline(x + wx + off, x + wx + off + 22, wy,
                     bytes((60, 110, 150)))
    # tanker, bow to the right
    tx, ty = x + 330, base + 26
    cv.poly([(tx, ty + 22), (tx + 190, ty + 22), (tx + 210, ty + 6),
             (tx + 16, ty + 6)], bytes((10, 10, 12)))          # hull
    cv.rect(tx + 24, ty - 12, 150, 18, RED)                     # deck
    for i, cc in enumerate((GOLD, BLUE, GREEN, TEAL)):
        cv.rect(tx + 30 + i * 36, ty - 30, 30, 18, cc)          # containers
    cv.rect(tx + 176, ty - 26, 22, 32, bytes((200, 200, 200)))  # bridge
    # fire on the foredeck
    fx, fy = tx + 60, ty - 30
    cv.poly([(fx - 14, fy), (fx, fy - 30), (fx + 14, fy)], ORANGE)
    cv.poly([(fx - 7, fy), (fx, fy - 18), (fx + 7, fy)], YELLOW)
    cv.circle(fx + 2, fy - 34, 6, bytes((120, 120, 120)))
    cv.circle(fx + 12, fy - 44, 8, bytes((110, 110, 110)))
    cv.circle(fx - 4, fy - 48, 7, bytes((100, 100, 100)))
    # caption chip inside the art
    cv.rect(x + 10, base + 52, 300, 18, bytes((0, 0, 0)))
    cv.text(x + 18, base + 55, "RIYADH SKYLINE  •  STRAIT OF HORMUZ",
            1, WHITE)


# ---------------------------------------------------------------- icons
def icon_gavel(cv, x, y, s, c):
    cv.rect(x, y + 2 * s, 14 * s, 4 * s, c)
    cv.rect(x + 5 * s, y + 6 * s, 4 * s, 12 * s, c)
    cv.rect(x, y + 18 * s, 14 * s, 3 * s, c)


def icon_rocket(cv, x, y, s, c):
    cv.poly([(x + 7 * s, y), (x + 12 * s, y + 8 * s), (x + 2 * s, y + 8 * s)],
            c)
    cv.rect(x + 2 * s, y + 8 * s, 10 * s, 8 * s, c)
    cv.poly([(x, y + 16 * s), (x + 2 * s, y + 10 * s), (x + 2 * s, y + 16 * s)],
            c)
    cv.poly([(x + 14 * s, y + 16 * s), (x + 12 * s, y + 10 * s),
             (x + 12 * s, y + 16 * s)], c)
    cv.poly([(x + 5 * s, y + 16 * s), (x + 7 * s, y + 22 * s),
             (x + 9 * s, y + 16 * s)], ORANGE)


def icon_plane(cv, x, y, s, c):
    cv.poly([(x, y + 6 * s), (x + 14 * s, y + 6 * s), (x + 12 * s, y + 9 * s),
             (x + 2 * s, y + 9 * s)], c)
    cv.poly([(x + 5 * s, y + 2 * s), (x + 9 * s, y + 2 * s),
             (x + 10 * s, y + 6 * s), (x + 4 * s, y + 6 * s)], c)
    cv.poly([(x + 9 * s, y + 9 * s), (x + 12 * s, y + 13 * s),
             (x + 10 * s, y + 13 * s), (x + 8 * s, y + 9 * s)], c)


# ---------------------------------------------------------------- content
HERO_TAG = "THE GULF  —  LEAD STORY"
HERO_HEAD = ["MISSILES", "OVER RIYADH"]
HERO_DECK = (
    "Saudi defences shoot down a Houthi ballistic missile aimed at the "
    "kingdom's west, hours after a drone is downed near Jeddah, as "
    "tankers burn in the Strait of Hormuz."
)
HERO_FOOT = "OIL JUMPS AS HORMUZ BURNS"

FEATURED = [
    ("SOUTH AFRICA", RED, "gavel",
     ["COURT SAVES", "RAMAPHOSA"],
     "The High Court throws out the Phala Phala impeachment report as "
     "unlawful. The probe into the president falls away."),
    ("SPACE", BLUE, "rocket",
     ["FIRST FOREIGNER", "ABOARD TIANGONG"],
     "Pakistan's Muhammad Zeeshan Ali docks with China's station on "
     "Shenzhou-24, the first foreign astronaut to visit Tiangong."),
    ("UNITED STATES", TEAL, "plane",
     ["THANKSGIVING", "TRAVEL CHAOS"],
     "Millions fly for Thanksgiving as storms and long lines hit US "
     "airports. Six die as a Cessna crashes off Mississippi."),
]

MINI = [
    ("EUROPE", "NATO BOOSTS AIR PATROLS ON EASTERN FLANK"),
    ("ASIA", "RUSSIAN JETS SPARK SHELTER ALERT IN S. KOREA"),
    ("MIGRATION", "RECORD DAY: NEARLY 2,000 MIGRANTS REACH CANARIES"),
    ("SPORT", "LILLE STUN BAYERN; STERLING SPARED JAIL"),
]

BRIEFS = [
    "UN: five women killed every hour",
    "WHO: end US fuel blockade on Cuba",
    "Trump moves to speed executions",
    "Houthis vow revenge after port hit",
    "China, Cambodia hold joint drills",
    "N. Korea orders Swiss office shut",
    "Australia, Solomons sign security pact",
    "Bangladesh garment pay up 36%",
    "Kuala Lumpur sues Google for $146m",
    "UN: HIV fight under pressure",
    "India marks Constitution Day",
    "Gukesh faces Sindarov for chess crown",
    "IPL 2027 auction draws 1,220 players",
    "Miss Universe: Puerto Rico wins",
    "Vance defends Nvidia chief Huang",
    "Brands sit out Black Friday",
    "Colombia troops free hostages",
    "Indonesia mine floods; nine dead",
    "Hasina asks to return on 16 December",
    "Baby meerkats debut at Peru zoo",
    "Senegal reinstated as African champions",
    "Oil jumps after Hormuz tanker blasts",
]

ICONS = {"gavel": icon_gavel, "rocket": icon_rocket, "plane": icon_plane}


# ---------------------------------------------------------------- page
def build():
    cv = Canvas(W, H, PAPER)
    # paper edge rules
    cv.rect(0, 0, W, 6, INK)
    cv.rect(0, H - 6, W, 6, INK)

    # ---- masthead
    cv.text(W // 2, 16, "THE WORLD TODAY", 8, INK, align="c")
    cv.hline(MARGIN, W - MARGIN, 84, INK)
    cv.hline(MARGIN, W - MARGIN, 87, INK)

    # ---- date bar
    cv.rect(MARGIN, 94, CONTENT_W, 34, INK)
    cv.text(MARGIN + 14, 103, "THURSDAY 26 NOVEMBER 2026", 2, WHITE)
    cv.text(W - MARGIN - 14, 103, "ONE DAY  •  ONE PAGE", 2, WHITE,
            align="r")

    # ---- hero
    hy = 136
    cv.rect(MARGIN, hy, CONTENT_W, 300, INK)  # frame
    draw_hero(cv, MARGIN + 3, hy + 3, 600, 294)
    cv.rect(MARGIN + 3 + 600, hy + 3, CONTENT_W - 600 - 6, 294, PAPER)
    hx = MARGIN + 3 + 600 + 14
    hw = CONTENT_W - 600 - 14 - 3 - 14
    cv.text(hx, hy + 16, HERO_TAG, 2, RED)
    cv.hline(hx, hx + hw, hy + 36, RED)
    y = cv.text_block(hx, hy + 48, HERO_HEAD, 5, INK, leading=42)
    y += 6
    y = cv.text_block(hx, y, wrap_text(HERO_DECK, hw, 2), 2, INK,
                      leading=17)
    y += 10
    cv.rect(hx, y, hw, 2, GOLD)
    y += 12
    y = cv.text_block(hx, y, wrap_text(HERO_FOOT, hw, 2), 2, RED,
                      leading=17)

    # ---- featured row (3 cards)
    fy = 448
    card_w = (CONTENT_W - 2 * 10) // 3
    for i, (tag, colour, icon, head, deck) in enumerate(FEATURED):
        cx = MARGIN + i * (card_w + 10)
        cv.rect(cx, fy, card_w, 2, colour)
        cv.text(cx, fy + 12, tag, 2, colour)
        ICONS[icon](cv, cx + card_w - 40, fy + 8, 2, colour)
        y = cv.text_block(cx, fy + 38, head, 3, INK, leading=26)
        y += 4
        cv.text_block(cx, y, wrap_text(deck, card_w, 2), 2, GREY,
                      leading=17)
        cv.vline(cx + card_w + 5, fy, fy + 186, LIGHT) if i < 2 else None
    cv.hline(MARGIN, W - MARGIN, fy + 190, INK)

    # ---- mini row (4 cards)
    my = 650
    mini_w = (CONTENT_W - 3 * 10) // 4
    for i, (tag, head) in enumerate(MINI):
        cx = MARGIN + i * (mini_w + 10)
        cv.rect(cx, my, 4, 118, GOLD)
        cv.text(cx + 12, my + 6, tag, 2, RED)
        cv.text_block(cx + 12, my + 30,
                      wrap_text(head, mini_w - 12, 2), 2, INK, leading=17)
    cv.hline(MARGIN, W - MARGIN, my + 128, INK)

    # ---- in brief
    by = 784
    cv.text(MARGIN, by, "IN BRIEF", 3, INK)
    cv.text(W - MARGIN, by, "MORE OF THE DAY", 2, GREY, align="r")
    cv.hline(MARGIN, W - MARGIN, by + 28, RED)
    col_w = (CONTENT_W - 10) // 2
    half = (len(BRIEFS) + 1) // 2
    for col in range(2):
        bx = MARGIN + col * (col_w + 10)
        for j, item in enumerate(BRIEFS[col * half:(col + 1) * half]):
            yy = by + 36 + j * 15
            cv.text(bx, yy, "\u2022", 2, RED)
            cv.text(bx + 14, yy, item, 2, INK)

    # ---- footer
    cv.rect(MARGIN, 992, CONTENT_W, 22, INK)
    cv.text(W // 2, 997,
            "ALL EVENTS OF THURSDAY 26 NOVEMBER 2026  •  COMPILED FROM "
            "WIRE REPORTS", 1, WHITE, align="c")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
