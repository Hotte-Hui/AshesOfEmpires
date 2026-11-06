"""env_c4p2_cine_pal -- the palettes of the Chapter-4-part-2 cinematics (owner: cine stream, round 10).

The cities keep their palettes so a match cut reads at a glance (C4P2_DESIGN §2.9):
  KARSK     sodium and kerosene amber, coal black, red banners, the cold blue of snow before dawn
  BERLIN_ST the Ostbahnhof: sodium under a glass roof, steam, soot, the express's green
  BERLIN_YD the courtyard at night: night blue with warm windows
  KORDON    floodlit snow far off: white-blue, a little amber, black
Every plate and every figure of a shot is snapped to its film's palette (kit.quant).
"""
from __future__ import annotations

# ------------------------------------------------------------------------------------------------- Karsk
K_NIGHT = ['#04060a', '#080c13', '#0d131d', '#131b28', '#1a2434', '#222e41', '#2c3a50', '#38475f', '#465570']
K_DAWN = ['#3a3450', '#4e4560', '#66566c', '#806674', '#9a7a7c']
K_SNOW = ['#2a3444', '#3a4658', '#4e5b6e', '#657286', '#7e8b9e', '#98a5b6', '#b4bfcc', '#cfd7e0', '#e6ecf1',
          '#f6f8fa']
K_AMBER = ['#1c1008', '#36200e', '#563414', '#7c4c1a', '#a46a24', '#c88a36', '#e6ae54', '#f8d084', '#fff0c4']
K_FIRE = ['#3a0e04', '#6e1e06', '#a8380a', '#dc6014', '#f89a2c', '#ffd060', '#fff4c0']
K_COAL = ['#050506', '#0a0a0c', '#111114', '#18181c', '#212126', '#2c2c33', '#3a3a44']
K_BRICK = ['#140a08', '#22100c', '#341a12', '#4a2418', '#62301e', '#7c4028', '#985234', '#b06844']
K_RUST = ['#1e0c08', '#34160e', '#4e2214', '#6a301a', '#884022', '#a4542c']
K_WOOD = ['#100a06', '#1e140c', '#2e2014', '#42301e', '#58422a', '#725638', '#8e6e48']
K_CONC = ['#0e1012', '#181b1e', '#23272b', '#30353a', '#3f454b', '#50575e', '#646b72', '#7c838a']
K_IRON = ['#06080a', '#0e1216', '#171c22', '#222830', '#2e3640', '#3c4652', '#4e5966']
K_RED = ['#2a0606', '#4a0c0a', '#6e1410', '#962018', '#b83022', '#d64a32', '#ec7458']
K_GREEN = ['#0a120c', '#122018', '#1c3022', '#28442e', '#36583a', '#4a7048']
K_SKIN = ['#2a1812', '#4a2a1e', '#6e4230', '#946046', '#b8805e', '#d6a47c', '#eccaa4']
K_CLOTH = ['#1a1814', '#2a2620', '#3c362e', '#4e463c', '#62584c', '#787060', '#948a78']
K_PAPER = ['#4a463c', '#787260', '#a49c86', '#c8c0a8', '#e4dcc4', '#f6f0de']
K_STEAM = ['#5a6270', '#7a8290', '#9aa2ae', '#bcc2ca', '#d8dce2', '#eef0f2']
KARSK = None  # filled below

# ------------------------------------------------------------------------------------------------- Berlin station
B_NIGHT = ['#05070c', '#0a0e18', '#101624', '#171f32', '#1f2940', '#28344f', '#33415f']
B_SODIUM = ['#24140a', '#46280e', '#6e4014', '#9a5c1c', '#c27e2a', '#e2a242', '#f6c86e', '#ffe6a8', '#fff6dc']
B_SOOT = ['#0a0a0b', '#131315', '#1c1c1f', '#26262a', '#323236', '#404044', '#505055', '#64646a', '#7c7c82']
B_STEAM = ['#4a4a52', '#66666c', '#86848a', '#a6a2a2', '#c6c0ba', '#e2dcd2', '#f6f2ea']
B_GREEN = ['#08100c', '#0e1c14', '#16281c', '#203626', '#2c4632', '#3a5a40', '#4e7252']
B_GLASS = ['#0c1218', '#141c26', '#1e2a36', '#2a3a48', '#3a4c5c', '#506476']
B_BRICK = ['#160c0a', '#26140e', '#381e14', '#4c2a1c', '#623826', '#7a4832', '#945a40']
B_CLOTH = ['#14141a', '#222230', '#323244', '#444058', '#5a5064', '#726474', '#8c7c86']
B_SKIN = ['#2a1814', '#4c2c22', '#724634', '#98644a', '#ba8462', '#d8a880', '#f0cca8']
B_RED = ['#2c0808', '#500e0c', '#781814', '#a0241a', '#c43a26', '#e06044']
B_PAPER = ['#3a3830', '#66625a', '#928c80', '#bab4a6', '#dcd6c6', '#f4f0e4']
B_WOOD = ['#120c08', '#22160e', '#342216', '#4a3220', '#62442c', '#7e5a3a', '#9a7450']
B_STEEL = ['#0a0d0e', '#131819', '#1d2324', '#283031', '#343e3f', '#444f50', '#586464', '#728080']
B_BLUE = ['#0c1424', '#14203a', '#1e2e52', '#2a3e6a', '#3a5284', '#52689c']

# ------------------------------------------------------------------------------------------------- Berlin courtyard
Y_NIGHT = ['#03050a', '#070b14', '#0c1220', '#121a2e', '#19233c', '#212e4c', '#2b3a5e', '#364870', '#435784']
Y_SNOW = ['#1c2438', '#26304a', '#323e5c', '#404e70', '#526184', '#687898', '#8292b0', '#a2b0c8', '#c4cee0',
          '#e2e8f2']
Y_WARM = ['#2a160a', '#4c2810', '#784018', '#a45e22', '#cc8232', '#eaa84c', '#fcce7c', '#fff0c0']
Y_RED = ['#2a0606', '#520c0a', '#821410', '#b4221a', '#e03a2a', '#ff6a50', '#ffb0a0']
Y_PLASTER = ['#14161e', '#1e222c', '#2a2e3a', '#363a48', '#444858', '#545868', '#686c7c']
Y_BRICK = ['#120a0c', '#1e1014', '#2c181c', '#3c2226', '#4e2e30', '#62403e']
Y_IRON = ['#05070a', '#0b0e14', '#12161e', '#1a2029', '#242b36', '#303845']
Y_SKIN = ['#26161a', '#462a2a', '#6a4238', '#90604c', '#b48064', '#d4a482', '#ecc8a6']
Y_CANDLE = ['#3a1c06', '#7a420e', '#c47820', '#f2b040', '#ffe08a', '#fff8dc']

# ------------------------------------------------------------------------------------------------- Kordon
D_NIGHT = ['#020306', '#05070c', '#090d16', '#0f1422', '#151c2e', '#1d263c']
D_SNOW = ['#1a2232', '#242e42', '#303c54', '#3e4c66', '#50607c', '#687a94', '#8496ae', '#a6b4c8', '#ccd6e2',
          '#eef2f6']
D_LIGHT = ['#3a3426', '#6a5e40', '#a08c5c', '#d0bc84', '#f2e2b0', '#fffae8']
D_WAGON = ['#140806', '#24100c', '#381a12', '#4e241a', '#663024']

# ------------------------------------------------------------------------------------------------- per film
KARSK = K_NIGHT + K_DAWN + K_SNOW + K_AMBER + K_FIRE + K_COAL + K_BRICK + K_RUST + K_WOOD + K_CONC + K_IRON + \
    K_RED + K_GREEN + K_SKIN + K_CLOTH + K_PAPER + K_STEAM
BERLIN_ST = B_NIGHT + B_SODIUM + B_SOOT + B_STEAM + B_GREEN + B_GLASS + B_BRICK + B_CLOTH + B_SKIN + B_RED + \
    B_PAPER + B_WOOD + B_STEEL + B_BLUE
BERLIN_YD = Y_NIGHT + Y_SNOW + Y_WARM + Y_RED + Y_PLASTER + Y_BRICK + Y_IRON + Y_SKIN + Y_CANDLE + B_CLOTH[:5] + \
    B_PAPER[:4]
KORDON = D_NIGHT + D_SNOW + D_LIGHT + D_WAGON + K_AMBER[:6] + ['#ffffff']


def dedup(p):
    out, seen = [], set()
    for c in p:
        c = c.lower()
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


KARSK = dedup(KARSK)
BERLIN_ST = dedup(BERLIN_ST)
BERLIN_YD = dedup(BERLIN_YD)
KORDON = dedup(KORDON)
