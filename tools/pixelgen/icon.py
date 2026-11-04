"""App / window icon for Ashes of Empires: The Last Winter (original pixel art, 32x32 master).

Motif: a cold winter dusk, a monumental dome silhouette (the fictional Great Hall) with one warm window,
and the red C-17 stamp ring -- the game's two cities and its mystery in one mark.
Run:  py -3 -P tools/pixelgen/icon.py   -> assets/icon/icon.png (256), icon_32.png, icon.ico (16..256)
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "icon")

def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

SKY = [hx("#0b1418"), hx("#132833"), hx("#24434c"), hx("#5d6b63"), hx("#a77a5c")]
DOME = hx("#05090c")
DOME_RIM = hx("#1e2a2e")
WARM = hx("#e8a457")
WARM_D = hx("#a8623a")
RED = hx("#b8322a")
RED_D = hx("#7a1e1c")
SNOW = hx("#d8e0dc")
SNOW_D = hx("#8fa3a3")
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def build():
    n = 32
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    # rounded-square plate with dithered dusk gradient (dark top -> lighter horizon)
    for y in range(n):
        for x in range(n):
            if (x in (0, n - 1) and y in (0, 1, n - 2, n - 1)) or (y in (0, n - 1) and x in (0, 1, n - 2, n - 1)):
                continue
            t = min(y, 21) / 21 * (len(SKY) - 1)
            i = int(t)
            f = t - i
            c = SKY[min(i + (1 if f * 16 > BAYER[y % 4][x % 4] else 0), len(SKY) - 1)]
            px[x, y] = c
    # stamp ring (C-17 red), centre (16, 13), radius ~9.5, 2 px thick, slightly worn
    cx, cy = 15.5, 12.5
    for y in range(n):
        for x in range(n):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 8.2 <= d <= 10.0:
                worn = (x * 7 + y * 13) % 11 == 0
                if not worn:
                    px[x, y] = RED if d < 9.3 else RED_D
    # dome silhouette on a podium
    for y in range(13, 27):
        for x in range(3, 29):
            dx = (x - 15.5) / 10.5
            top = 21 - round(7.0 * max(0.0, 1 - dx * dx) ** 0.5) if abs(dx) <= 1 else 99
            if y >= top:
                px[x, y] = DOME
    for x in range(15, 17):              # lantern
        for y in range(11, 14):
            px[x, y] = DOME
    for y in range(21, 27):              # podium
        for x in range(1, 31):
            px[x, y] = DOME
    for x in range(2, 30):               # podium cornice rim light
        px[x, 21] = DOME_RIM
    solid = {(x, y) for y in range(n) for x in range(n) if px[x, y] == DOME}
    for (x, y) in solid:                 # 1 px rim on the upper-left edge (cold sky light)
        if 12 <= y <= 20 and ((x - 1, y) not in solid or (x, y - 1) not in solid) and x < 16:
            px[x, y] = DOME_RIM
    # the one warm window
    for (x, y) in [(15, 23), (16, 23), (15, 24), (16, 24)]:
        px[x, y] = WARM
    px[15, 25] = WARM_D
    px[16, 25] = WARM_D
    # snow ground + flakes
    for y in range(27, 31):
        for x in range(0, 32):
            if px[x, y][3]:
                px[x, y] = SNOW if (y == 27 or (x + y) % 5) else SNOW_D
    for (x, y) in [(5, 4), (24, 3), (9, 9), (27, 10), (4, 15), (28, 17), (20, 6), (11, 2)]:
        px[x, y] = SNOW if (x + y) % 2 else SNOW_D
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    im = build()
    im.save(os.path.join(OUT, "icon_32.png"))
    big = im.resize((256, 256), Image.NEAREST)
    big.save(os.path.join(OUT, "icon.png"))
    big.save(os.path.join(OUT, "icon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon written to", OUT)


if __name__ == "__main__":
    main()
