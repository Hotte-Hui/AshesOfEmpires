"""Pipeline test environment (NOT game art): validates layers, parallax, normals, emission, props, lights."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pg, numpy as np
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'environments', '_test')
W, H = 1280, 360
P = lambda r: pg.pal('karsk', r)
sky = pg.Layer(640, 360); pg.sky(sky, P('sky')[::-1][1:] + [P('sage')[4]], horizon_glow=(470, 240, 260, 90, [P('sky')[4], P('sky')[5], P('copper')[3]]))
pg.clouds(sky, 30, 190, [P('sage')[2], P('sage')[3], P('sky')[1], P('sky')[3], P('sky')[4], P('sky')[5]], seed=3, count=7)
far = pg.Layer(640 + int(0.2 * (W - 640)) + 8, 360); rng = np.random.default_rng(1); x = 0
while x < far.w:
    w = int(rng.integers(18, 50)); h = int(rng.integers(40, 110)); far.rect(x, 250 - h, w, h + 110, P('sky')[1], hgt=0.2); x += w + int(rng.integers(0, 6))
mid = pg.Layer(640 + int(0.5 * (W - 640)) + 8, 360)
mid.rect(140, 110, 200, 250, P('stone')[2], hgt=0.5)
pg.window_grid(mid, 150, 124, 11, 8, 10, 14, 7, 9, P('stone')[1], P('night')[2], P('sky')[2], lit=P('copper')[3], lit_prob=0.05, broken_prob=0.15, boarded=P('wood')[2], boarded_prob=0.08, seed=4)
pg.snow_caps(mid, P('snow'), seed=2)
pg.smoke_ribbon(mid, [(520, 150), (480, 100), (560, 60), (510, 0)], 10, 26, [P('night')[2], P('teal')[1], P('teal')[2], P('teal')[3]], seed=5)
pg.truss(mid, 360, 200, 640, 130, 5, P('rust')[2])
ground = pg.Layer(W, 360)
ground.rect(0, 240, W, 120, P('stone')[1], hgt=0.0); ground.rect(0, 240, W, 4, P('stone')[0])
for ty in (270, 300):
    ground.rect(0, ty, W, 2, P('rust')[3], hgt=0.4); ground.rect(0, ty + 2, W, 1, P('night')[1])
    for sx in range(0, W, 9): ground.rect(sx, ty - 2, 5, 7, P('wood')[1], hgt=0.2)
pg.rubble(ground, 0, W, 352, P('stone'), n=90, seed=6)
fg = pg.Layer(W + 400, 360); pg.grass_tufts(fg, 0, fg.w, 359, P('night')[:2], density=0.9, hmax=16, seed=7)
crate = pg.Layer(28, 24); crate.rect(0, 0, 28, 24, P('wood')[2], hgt=0.6); crate.rect(0, 0, 28, 2, P('wood')[4], hgt=0.8)
for k in (6, 13, 20): crate.hline(0, k, 28, P('wood')[1], hgt=0.4)
crate.outline(P('night')[1], outer=False)
os.makedirs(OUT + '/props', exist_ok=True)
for L, n, nm in ((sky, 'sky', False), (far, 'far', True), (mid, 'mid', True), (ground, 'ground', True), (fg, 'fg', False)):
    L.save(f'{OUT}/{n}', normal=nm)
crate.save(f'{OUT}/props/crate')
open(f'{OUT}/.gdignore_preview', 'w').close()
pg.write_manifest(f'{OUT}/scene.json', {
 "id": "_test", "palette": "karsk", "world_size": [W, 360], "camera": {"bounds": [0, 0, W, 360]},
 "layers": [
  {"name": "sky", "file": "sky.png", "pos": [0, 0], "parallax": [0, 0], "z": -100, "lit": False},
  {"name": "far", "file": "far.png", "pos": [0, 0], "parallax": [0.2, 0], "z": -90, "normal": True},
  {"name": "mid", "file": "mid.png", "pos": [0, 0], "parallax": [0.5, 0], "z": -80, "normal": True, "emission": True},
  {"name": "ground", "file": "ground.png", "pos": [0, 0], "parallax": [1, 1], "z": -10, "normal": True},
  {"name": "fg", "file": "fg.png", "pos": [0, 0], "parallax": [1.3, 1], "z": 60, "lit": False}],
 "props": [{"name": "crate", "file": "props/crate.png", "pos": [400, 290], "base_y": 314, "collision": [[402, 306], [426, 306], [426, 314], [402, 314]]}],
 "walkable": [[0, 250], [W, 250], [W, 352], [0, 352]],
 "spawns": {"SP_Test": [200, 320]},
 "hotspots": {"crate": [414, 316]},
 "lights": [{"pos": [430, 290], "color": "#F0C487", "energy": 1.3, "radius": 110, "flicker": 0.15, "height": 30}],
 "fx": [{"type": "snow", "density": 0.7}, {"type": "fog_band", "y": 236, "height": 36, "color": "#AFC1AA", "alpha": 0.4, "parallax": 0.7}]})
print('test env ok')
