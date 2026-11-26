#!/usr/bin/env python3
"""The World in One Day - Thursday 26 November 2026.

Draws a broadsheet front page (1024x1024 PNG) with pure Python stdlib.
No network, no randomness, no timestamps: two runs are byte-identical.

Layout (fresh design): navy masthead with the date, one hero story with a
drawn dusk-airbase illustration, four secondary stories with small drawn
motifs, and an IN BRIEF strip. All text uses a hand-drawn 5x7 bitmap font
defined below; the PNG encoder is written by hand (zlib + struct).
"""
import os
import struct
import zlib

W = H = 1024
OUT = "/output/entry.png"

# ---- palette ------------------------------------------------------------
PAPER = (246, 241, 227)
INK = (24, 24, 24)
NAVY = (22, 38, 63)
NAVY_DARK = (15, 27, 46)
RED = (178, 38, 30)
GOLD = (214, 158, 46)
WHITE = (250, 248, 242)
GREY = (112, 110, 102)
SKY_TOP = (31, 42, 68)
DUSK = (107, 74, 58)
HORIZON = (232, 163, 76)
GROUND = (42, 40, 36)
RUNWAY = (126, 124, 118)
ORANGE = (232, 115, 26)
FLAME_Y = (242, 194, 48)
FLAME_W = (247, 224, 138)
SMOKE = (104, 104, 100)
LIGHT = (232, 228, 216)
DARKPANEL = (46, 42, 38)
SKYBLUE = (127, 179, 213)

# ---- hand-drawn 5x7 bitmap font ----------------------------------------
# Each glyph is 7 rows of 5 characters; '#' is ink, ' ' is blank.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".....", ".....", ".##..", ".....", "....."),
    ";": (".....", ".##..", ".....", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#..##", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
}

# ---- canvas -------------------------------------------------------------
buf = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def rect(x, y, w, h, c):
    for yy in range(max(0, y), min(H, y + h)):
        base = (yy * W + max(0, x)) * 3
        for xx in range(max(0, x), min(W, x + w)):
            buf[base], buf[base + 1], buf[base + 2] = c
            base += 3


def outline(x, y, w, h, c, t=2):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def hline(x0, x1, y, c, t=1):
    rect(x0, y, x1 - x0, t, c)


def vline(x, y0, y1, c, t=1):
    rect(x, y0, t, y1 - y0, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        for x in range(cx - dx, cx + dx + 1):
            set_px(x, cy + dy, c)


def ring(cx, cy, r, c, t=2):
    import math
    for deg in range(0, 360, 2):
        a = math.radians(deg)
        for rr in range(r - t + 1, r + 1):
            set_px(int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a)), c)


def fill_poly(points, c):
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, ya = points[i]
            x1, yb = points[(i + 1) % n]
            if (ya <= y < yb) or (yb <= y < ya):
                t = (y - ya) / (yb - ya)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa, xb = int(xs[i]), int(xs[i + 1])
            for x in range(xa, xb + 1):
                set_px(x, y, c)


# ---- text ---------------------------------------------------------------
def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_text(s, x, y, scale, color, align="left"):
    s = s.replace("\u2014", "-").replace("\u2019", "'")
    w = text_w(s, scale)
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == "#":
                    rect(cx + cc * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale


def wrap(s, max_w, scale):
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(s, x, y, max_w, scale, color, lh=None):
    lh = lh or (7 * scale + 4)
    for ln in wrap(s, max_w, scale):
        draw_text(ln, x, y, scale, color)
        y += lh
    return y


# ---- motifs -------------------------------------------------------------
def motif_tariffs(x, y, w, h):
    rect(x, y, w, h, (240, 223, 176))
    base = y + h - 14
    heights = [28, 48, 66, 84]
    cols = [NAVY, NAVY, NAVY, RED]
    for i, hh in enumerate(heights):
        bx = x + 24 + i * 52
        rect(bx, base - hh, 30, hh, cols[i])
    hline(x + 14, x + w - 14, base, INK, 2)
    draw_text("$", x + 18, y + 8, 3, RED)


def motif_cairo(x, y, w, h):
    rect(x, y, w, h, DARKPANEL)
    # road
    rect(x + 10, y + h - 34, w - 20, 24, (85, 82, 76))
    for dx in range(0, w - 20, 28):
        rect(x + 14 + dx, y + h - 23, 16, 3, WHITE)
    # tanker
    rect(x + 58, y + h - 56, 96, 20, (196, 84, 30))
    rect(x + 154, y + h - 56, 26, 20, (220, 120, 40))
    circle(x + 78, y + h - 34, 6, INK)
    circle(x + 140, y + h - 34, 6, INK)
    circle(x + 168, y + h - 34, 6, INK)
    # flame above the tanker
    circle(x + 110, y + 62, 24, ORANGE)
    circle(x + 110, y + 56, 16, FLAME_Y)
    circle(x + 110, y + 50, 8, FLAME_W)
    fill_poly([(x + 100, y + 58), (x + 110, y + 26), (x + 120, y + 58)], ORANGE)
    # smoke
    circle(x + 96, y + 30, 10, SMOKE)
    circle(x + 124, y + 24, 12, SMOKE)
    circle(x + 112, y + 14, 8, SMOKE)


def motif_scales(x, y, w, h):
    rect(x, y, w, h, LIGHT)
    cx = x + w // 2
    vline(cx, y + 18, y + h - 16, NAVY, 3)
    hline(cx - 38, cx + 38, y + 20, NAVY, 3)
    for sx in (cx - 38, cx + 38):
        line(sx, y + 20, sx - 12, y + 52, NAVY)
        line(sx, y + 20, sx + 12, y + 52, NAVY)
        fill_poly([(sx - 14, y + 52), (sx + 14, y + 52), (sx, y + 66)], NAVY)
    rect(cx - 22, y + h - 16, 44, 6, NAVY)
    draw_text("4000", cx, y + 2, 2, RED, align="center")


def motif_space(x, y, w, h):
    rect(x, y, w, h, NAVY_DARK)
    for sx, sy in ((x + 24, y + 18), (x + 60, y + 34), (x + 190, y + 22),
                   (x + 150, y + 14), (x + 96, y + 12), (x + 210, y + 44)):
        rect(sx - 1, sy - 4, 2, 8, WHITE)
        rect(sx - 4, sy - 1, 8, 2, WHITE)
    cx, cy = x + w // 2, y + h // 2 + 8
    ring(cx, cy, 52, SKYBLUE, 2)
    rect(cx - 46, cy - 5, 34, 10, GOLD)
    rect(cx + 12, cy - 5, 34, 10, GOLD)
    rect(cx - 12, cy - 9, 24, 18, WHITE)
    circle(cx, cy - 16, 6, GOLD)
    circle(cx - 8, cy - 4, 2, NAVY)
    circle(cx + 8, cy - 4, 2, NAVY)


def draw_jet(x, y, s, color):
    pts = [(0, 6), (20, 0), (34, 4), (46, 6), (34, 8), (20, 12),
           (16, 8), (6, 10), (2, 8)]
    fill_poly([(x + px * s, y + py * s) for px, py in pts], color)


def hero_art(x, y, w, h):
    # dusk sky in bands
    rect(x, y, w, 100, SKY_TOP)
    rect(x, y + 100, w, 80, DUSK)
    rect(x, y + 180, w, 70, HORIZON)
    rect(x, y + 250, w, h - 250, GROUND)
    # low sun
    circle(x + w - 60, y + 150, 18, FLAME_W)
    # hangar, left
    rect(x + 16, y + 196, 92, 54, (18, 18, 18))
    circle(x + 62, y + 196, 46, (18, 18, 18))
    rect(x + 28, y + 216, 68, 34, (52, 48, 44))
    vline(x + 62, y + 216, y + 250, (18, 18, 18), 2)
    # runway
    rect(x, y + 268, w, 18, RUNWAY)
    for dx in range(8, w, 36):
        rect(x + dx, y + 275, 18, 3, WHITE)
    # parked jets, light silhouettes on the runway
    draw_jet(x + 130, y + 268, 1, (210, 208, 200))
    draw_jet(x + 210, y + 270, 1, (210, 208, 200))
    # explosion plume
    ex, ey = x + w - 110, y + 130
    circle(ex, ey + 46, 58, (201, 58, 18))
    circle(ex, ey + 34, 46, ORANGE)
    circle(ex, ey + 22, 32, FLAME_Y)
    circle(ex, ey + 12, 18, FLAME_W)
    fill_poly([(ex - 44, ey + 40), (ex - 10, ey - 30), (ex + 6, ey + 40)], ORANGE)
    fill_poly([(ex + 8, ey + 44), (ex + 34, ey - 14), (ex + 52, ey + 44)], FLAME_Y)
    # smoke rising
    circle(ex - 52, ey - 34, 16, SMOKE)
    circle(ex - 30, ey - 52, 20, SMOKE)
    circle(ex + 2, ey - 58, 14, SMOKE)
    circle(ex + 30, ey - 44, 12, SMOKE)


# ---- PNG writer ---------------------------------------------------------
def write_png(path, w, h):
    raw = b"".join(b"\x00" + bytes(buf[yy * w * 3:(yy + 1) * w * 3])
                   for yy in range(h))

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---- page ---------------------------------------------------------------
def main():
    rect(0, 0, W, H, PAPER)
    outline(8, 8, W - 16, H - 16, INK, 3)

    # masthead
    rect(16, 16, W - 32, 144, NAVY)
    draw_text("THE WORLD IN ONE DAY", W // 2, 42, 7, WHITE, align="center")
    hline(64, 252, 112, RED, 2)
    hline(772, 960, 112, RED, 2)
    draw_text("THURSDAY 26 NOVEMBER 2026", W // 2, 104, 3, WHITE,
              align="center")

    # hero
    draw_text("WAR IN UKRAINE", 40, 186, 2, RED)
    draw_text("UKRAINE STRIKES", 40, 216, 5, INK)
    draw_text("SAVASLEYKA AIRBASE", 40, 261, 5, INK)
    draw_para("KYIV SAYS THREE MIG-31 JETS AND TWO SU-34 FIGHTER-BOMBERS "
              "WERE KNOCKED OUT OF ACTION IN A LONG-RANGE STRIKE ON THE "
              "SAVASLEYKA AIRBASE EAST OF MOSCOW. THE CLAIM HAS NOT BEEN "
              "INDEPENDENTLY VERIFIED.", 40, 330, 560, 2, INK)
    # stat chip
    outline(40, 430, 556, 40, RED, 2)
    draw_text("5 JETS HIT - 3 MIG-31, 2 SU-34", 56, 440, 3, RED)
    # hero illustration
    outline(620, 180, 364, 340, INK, 2)
    hero_art(622, 182, 360, 336)

    hline(40, 984, 544, INK, 2)

    # secondary stories
    draw_text("ALSO TODAY", 40, 556, 2, RED)
    cols = [
        ("TRADE", "TRUMP TARIFFS HIT 14 PARTNERS",
         "NEW LEVIES ON 14 TRADE PARTNERS", motif_tariffs),
        ("EGYPT", "CAIRO TANKER FIRE KILLS 31",
         "21 INJURED IN RING ROAD BLAZE", motif_cairo),
        ("ISRAEL", "JUDGE: DROP NETANYAHU CASE",
         "CASE 4000 BRIBERY CHARGES", motif_scales),
        ("SPACE", "SPACEX GETS 1M SATELLITE NOD",
         "MEGACONSTELLATION GETS GO-AHEAD", motif_space),
    ]
    for i, (kick, head, sub, motif) in enumerate(cols):
        cx = 40 + i * 242
        motif(cx, 584, 226, 110)
        outline(cx, 584, 226, 110, INK, 2)
        draw_text(kick, cx, 704, 2, RED)
        end_y = draw_para(head, cx, 726, 226, 3, INK, lh=26)
        draw_para(sub, cx, end_y + 8, 226, 2, GREY, lh=18)

    hline(40, 984, 858, INK, 2)

    # IN BRIEF strip
    rect(40, 872, 944, 100, NAVY)
    draw_text("IN BRIEF", 56, 884, 3, WHITE)
    briefs = [
        "POLAND SETS UP A BORDER NO-FLY ZONE",
        "HOSTAGES FREED IN CARTAGENA SUPERMARKET SIEGE",
        "MACY'S 100TH THANKSGIVING DAY PARADE IN NEW YORK",
    ]
    for i, b in enumerate(briefs):
        bx = 56 + i * 312
        rect(bx, 922, 8, 8, RED)
        draw_para(b, bx + 18, 916, 272, 2, WHITE, lh=18)

    # footer
    draw_text("SOURCES: UKRAINIAN GENERAL STAFF AND NEWS WIRES - 26 NOVEMBER 2026",
              W // 2, 990, 2, GREY, align="center")

    size = write_png(OUT, W, H)
    print("wrote", OUT, size, "bytes")


if __name__ == "__main__":
    main()
