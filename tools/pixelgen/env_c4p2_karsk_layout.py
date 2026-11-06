"""env_c4p2_karsk_layout -- coordinates of L_C4P2_Karsk (documentation/C4P2_DESIGN.md 4.1).

World 1920 x 360 px, side view: feet line y 300, walk band y 296-306 (x 18-1902), everything painted stands behind
it (base_y <= 294), the foreground layer stays below y 318.  Two walk areas separated by the permanent blocker
`tarpaulin` (858-898): A = the back yard and the coal stage (Monday 6.10, dawn), B = the showcase and platform 1
(Tuesday 17.30-20.10, evening floodlight).  The two halves are painted as two places (two bakes, two looks) -- the
camera of one scene never sees the other (camera_zones).  Every story name of the placeholder is kept.
"""
from __future__ import annotations

WORLD_W, WORLD_H = 1920, 360
FEET = 300
WALK_X = (18, 1902)
WALK_BAND = (296, 306)
SA, SB = 'L_C4P2_KarskA', 'L_C4P2_KarskB'

CAMERA = {SA: (0, 878), SB: (878, 1920)}          # camera_zones [x0, x1)
SPAN = {SA: (0, 904), SB: (856, 1920)}            # painted world range of each bake (a little past the zone)

SPAWNS = {'SP_C4P2_Yard': (48, 300), 'SP_C4P2_Signal': (930, 300)}
HOTSPOTS = {
    'dispatch_window': (132, 300), 'irina_window': (196, 300), 'coal_list': (400, 300), 'maria_coal': (560, 300),
    'guard_coal': (690, 300), 'press_notice': (780, 300),
    'signal_post': (980, 300), 'minder_canteen': (1110, 300), 'canteen_table': (1170, 300),
    'lev_sandhouse': (1350, 300), 'sand_table': (1460, 300), 'sand_lamp': (1520, 300), 'express_door': (1780, 300),
}
NPCS = {
    'irina_window': {'char': 'irina', 'feet': [214, 300], 'facing': 'left'},
    'maria_coal': {'char': 'maria', 'feet': [578, 300], 'facing': 'left'},
    'guard_coal': {'char': 'guard_karsk', 'feet': [690, 300], 'facing': 'left'},
    'signal_post': {'char': 'journalist', 'feet': [998, 300], 'facing': 'left', 'hide_after': 'c4g_inspect_card'},
    'minder_canteen': {'char': 'press_officer', 'feet': [1110, 300], 'facing': 'left'},
    'lev_sandhouse': {'char': 'lev', 'feet': [1368, 300], 'facing': 'left', 'show_after': 'c4g_inspect_book'},
    'express_door': {'char': 'journalist', 'feet': [1798, 300], 'facing': 'left', 'show_after': 'c4g_inspect_card'},
}
BLOCKERS = [{'name': 'tarpaulin', 'rect': [858, 270, 40, 60],
             'note': 'the tarpaulin fence (Kolonne 4 behind the tarpaulin): back yard (Monday, scene A) and showcase + '
                     'platform 1 (Tuesday, scene B) are two walk areas; the films carry the time'}]
ZONES = {'yard': [0, 858], 'tarpaulin': [858, 898], 'showcase': [898, 1600], 'platform_1': [1600, 1920]}

# ---------------------------------------------------------------- A: back yard and coal stage (Monday, 6.10)
A_BACK = 286             # base of the buildings at the back of the yard
A_MID = 292              # base of things at the back edge of the walk band
LAMP_A = (22, 176)                       # yard lamp (bulb)
SLEEPERS = (50, 88)
FIRE_SHIELD = (60, 86)                   # the red fire board on posts
DISPATCH = (92, 230)                     # the brick lean-to (wall span)
DISPATCH_WIN = (112, 236, 40, 26)        # x, y, w, h -- the order lies on the inside sill (x 124-140)
DUTY_BOARD = (156, 236, 18, 22)          # blackboard „График дежурств“, seven names, one „болен“
DISPATCH_DOOR = (178, 248, 16, 44)
CANTEEN = (236, 344)                     # the canteen's back (two storeys)
HATCH = (260, 246, 40, 22)               # serving hatch (kasha pot, the cook, the radio)
WATER_CRANE = 360                        # column of the water crane (+ the brazier at its foot)
STAGE = (380, 604)                       # coal-stage trestle span
DECK_Y = 178                             # top of the deck planks
STAIR = (384, 406)                       # steep stair up to the deck
LIST_POST = 400                          # list board on its post (coal_list)
MITTEN = (522, 270)                      # Lena's mitten nailed to the strut post at 520 (hidden find)
REST = 329                               # the rest corner: an old man of Kolonne 4 on a sleeper by the canteen's
                                         # bottle crates (round-10 lead pass: out of the shovellers' way, Lena's
                                         # mitten at 520 stays in view)
SHOVEL_B = 533                           # the woman shovelling toward the tender (feet; clear of Maria at 578)
STRUT = 520                              # an extra strut post under the deck (the mitten's post)
TENDER = (452, 600)                      # the special run's tender under the chutes
CHUTES = (470, 520, 568)
FLOOD_MAST = 622                         # lattice floodlight mast
ASH_PIT = (606, 662)
DOG = (636, 290)
BARREL = 672                             # the guard's fire barrel (centre; clear of the guard at 690)
ROUNDHOUSE = (712, 904)
GABLE_EMBLEM = (819, 104)                # the emblem disc on the roundhouse parapet, between two smoke hoods
STALL_DOORS = ((722, 774), (806, 858))
PERSONNEL_DOOR = (778, 800)              # small back door, the press notice pinned on it
NOTICE = (781, 258, 16, 14)
TARP_A = (840, 904)                      # the back of the tarpaulin seen from A

# ---------------------------------------------------------------- B: showcase and platform 1 (Tuesday evening)
TARP_B = (856, 1014)                     # the painted front of the tarpaulin, the gang behind it
SIGNAL = 984                             # mast of the restored signal (green aspect)
SIGNAL_SCRATCH = (985, 284)              # „А. М.“ scratched into the rust at the mast's foot (hidden find)
LOCO = (1016, 1092)                      # the polished engine, head-on, ribbons and wreath
RH_FRONT = (1000, 1100)                  # roundhouse front behind the engine
BAND = (1092, 1150)                      # plank stage, five players
CANTEEN_B = (1150, 1262)                 # the press canteen (cut open)
TABLE = (1154, 1198)                     # white tablecloth; the guidebook at x 1166-1176
CURTAIN = 1222                           # the curtain to the kitchen corner (bunched at 1222-1230)
KITCHEN_STOVE = (1240, 1256)             # the kitchen range with the band's kasha, inside the canteen's right wall
KITCHEN_COOK = 1234                      # the cook beside the curtain, stirring
TURNTABLE = (1262, 1320)
OILER = 1258                             # an old fitter oiling the bridge's left running wheel (1269)
SANDHOUSE = (1320, 1562)
SAND_DOOR_SMOKER = 1326                  # a sand-house man smoking in the doorway
SAND_STOVE = (1338, 1378)
SAND_HEAP = (1387, 288)                  # dry sand by the stove (centre, base): the depot cat sleeps on it
BENCH = (1438, 1506)                     # Lev's workbench (sand_table 1460)
GREEN_LAMP = (1520, 238)                 # the green-shaded lamp (sand_lamp)
SAND_SIEVE = 1542                        # a woman sifting dried sand into a box (x 1522-1538)
SCALE = (1396, 1418)                     # platform sack scale (side task „Ein Paket über die Linie“)
FLOOD_MAST_B = 1452                      # a lattice floodlight mast behind the sand-drying house
GATE = (1562, 1600)
PLATFORM = (1600, 1920)
CLOCKS = (1573, 1591)                    # on the gate's bracket: the station clock (19.10) and „Korridorzeit“ (17.10)
EXPRESS_DOOR = (1772, 1792)              # vestibule door of the sleeping car (Ekdahl's compartment)
CANOPY_Y = 150
CANOPY_COLUMNS = (1606, 1766, 1904)      # cast-iron columns, clear of the express lettering
LETTERBOARD_Y = 203                      # the express's lettering runs above its windows, over everybody's heads

# story props by hotspot (what the art shows there) -- written into scene.json hotspot_info
HOTSPOT_PROPS = {
    'dispatch_window': ('Irina\'s lit dispatch window: samovar, telephone, the typed order (carbon) on the inside '
                        'sill (gone after c4e_inspect_order)', (110, 154)),
    'irina_window': ('the padded door of the dispatch office; Irina stands beside it', (176, 230)),
    'coal_list': ('the list board under yellowed cellophane on its post at the foot of the coal-stage stair',
                  (392, 408)),
    'maria_coal': ('the spilled-coal heap under the stage, Kolonne 4 shovelling around Maria', (540, 600)),
    'guard_coal': ('the fire barrel; the guard warms his hands', (664, 700)),
    'press_notice': ('the typed press notice with the depot stamp, pinned on the roundhouse\'s back door',
                     (778, 800)),
    'signal_post': ('the restored colour-light signal, green aspect, red ribbons for the press', (952, 1012)),
    'minder_canteen': ('in front of the band stage', (1094, 1126)),
    'canteen_table': ('the press table: white cloth, tea glasses, bread with caviar, Ekdahl\'s guidebook (gone '
                      'after c4g_inspect_book)', (1154, 1198)),
    'lev_sandhouse': ('the door of the sand-drying house, the sand stove', (1322, 1380)),
    'sand_table': ('Lev\'s workbench: the two halves of card 0417 (after c4g_talk_lev), joined after '
                   'c4g_solve_halves', (1438, 1506)),
    'sand_lamp': ('the green-shaded lamp over the bench', (1508, 1532)),
    'express_door': ('the vestibule door of the sleeping car, the conductor, Ekdahl\'s compartment', (1764, 1800)),
}

