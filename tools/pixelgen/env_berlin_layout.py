"""env_berlin_layout -- single source of truth for M1 'Berliner Bauarchiv' world coordinates.

World 2924 x 360 logical px, Mode A side-on interior.  Feet line y = 300.
Rooms left -> right (round 2, 2026-11-04 evening):
  arrival hall (stairwell door, porter's lodge, regulator clock)  |  reading room & library  |
  drafting office (Konrad's desk)  |  archive hall  |  light-table room  |  Emil's issue counter
Konrad now enters through the TREPPENHAUS door at the far left (spawn SP_M1_Arrival) and walks the whole
floor once, left to right: porter -> library -> his desk (plan_a) -> archive (plan_b) -> light table -> Emil.
The four rooms of the first slice keep their art; they moved right by OFF.
"""

OFF = 1324             # x offset of the first-slice rooms (office .. Emil) in the extended world


def X(x):
    """first-slice x coordinate -> extended world x"""
    return x + OFF


WORLD_W, WORLD_H = 1600 + OFF, 360
VIEW_W, VIEW_H = 640, 360
FLOOR = 288            # back wall meets floor
WALK_Y = 300           # feet line of walking characters
WALK_BAND = (296, 306)
CEIL = 20              # ceiling/wall junction
HORIZON = 200          # eye level used for floor perspective

# ---------------------------------------------------------------- rooms (x ranges)
HALL = (0, 520)
PART0 = (520, 544)     # partition hall | library (poche + arch)
LIBRARY = (544, 1300)
PARTL = (1300, OFF + 4)  # partition library | office
OFFICE = (X(0), X(568))
PART1 = (X(568), X(596))     # partition office | archive (poche + arch)
ARCHIVE = (X(596), X(1092))
PART2 = (X(1092), X(1112))   # partition archive | light room
LIGHTROOM = (X(1112), X(1280))
EMIL = (X(1280), X(1600))

# ---------------------------------------------------------------- arrival hall
STAIR_DOOR = (40, 92)                 # TREPPENHAUS double door (x0, x1)
STAIR_DOOR_TOP = 170
PLAQUE = (104, 168, 28, 40)           # bronze plaque beside the stairwell door (x, y, w, h)
LODGE = (136, 238)                    # porter's lodge (prop) x range
LODGE_TOP = 222                       # top of the lodge cornice (prop)
LODGE_GLASS = (228, 260)              # glazing y range of the lodge front
REGULATOR = (262, 286)                # pendulum wall clock case x range
REG_FACE = (274, 158, 8)              # clock face centre x, y, radius
HALL_WINDOWS = [(316, 360)]
PHOTOS = (388, 166, 84, 44)           # framed photo display ('chronicle') x, y, w, h
HALL_LAMP = 252                       # pendant x

# ---------------------------------------------------------------- library
LIB_SHELVES = [(556, 628), (632, 704), (984, 1056), (1142, 1212), (1214, 1294)]
LIB_LABELS = ['I VERWALTUNG', 'II REICHSBAHN', 'III RAUMORDNUNG', 'IV GESUNDHEIT', 'V ARBEITSEINSATZ']
LIB_WINDOWS = [(726, 770), (1078, 1122)]
LIB_WIN_Y = (84, 250)                 # library windows reach lower than the office ones
LIB_SHELF_TOP = 60                    # bookcase crown
LIB_LABEL_Y = 147                     # section label band
LIB_RAIL_Y = 98                       # brass rail for the rolling ladder
CATALOGUE = (790, 840)
LIB_DESK = (854, 946)
GLOBE_X = 963
LIB_MAP = (858, 92, 72, 50)           # framed wall map above the librarian's desk
LIB_READ_TABLE = (1058, 1142)
LIB_LAMPS = [690, 1000, 1200]          # ceiling pendants

# ---------------------------------------------------------------- office (first slice, shifted)
DOOR0 = (X(22), X(70))                # corridor double door (x0, x1)
DOOR0_TOP = 178
WINDOWS = [(X(120), X(164)), (X(240), X(284)), (X(360), X(404))]   # glass x ranges
WIN_Y = (84, 236)                     # glass y range
PILASTERS = [(X(75), X(89)), (X(195), X(209)), (X(315), X(329)), (X(435), X(449))]
POSTER = (X(458), 160, 36, 54)        # x, y, w, h  (reconstruction poster, Reichssiegel / hist eagle)
CLOCK = (X(536), 166)                 # centre
CABINETS = (X(506), X(562))           # filing cabinets x range (baked)

# ---------------------------------------------------------------- archive
GALLERY_Y = (138, 148)                # gallery slab
RAIL_Y = 116                          # top rail of the gallery balustrade
PIERS = [X(600), X(716), X(832), X(948), X(1064)]    # left x of 12 px piers
PIER_W = 12
LADDER_X = X(668)
MOUSE_HOLE = (X(918), 283)            # mouse hole in the plinth of the box shelving (x, y top)
TUBE_STATION = (X(1064), 206)         # pneumatic tube receiving station on the last pier (x, y)

# ---------------------------------------------------------------- light room
DIAZO = (X(1222), X(1274))

# ---------------------------------------------------------------- Emil
NOTICE = (X(1300), 196, 36, 42)       # notice board x, y, w, h  (obs_notice)
PIGEON = (X(1350), 150, 128, 112)     # pigeonhole wall x, y, w, h
EXIT_DOOR = (X(1528), X(1576))        # now the MAGAZIN (stacks) door
EMIL_POS = (X(1412), 284)             # Emil's feet (behind the counter, sorted behind it)

ALL_WINDOWS = HALL_WINDOWS + LIB_WINDOWS + WINDOWS


def win_y(x0):
    """glass y range of the window starting at x0"""
    return LIB_WIN_Y if (x0, x0 + 44) in LIB_WINDOWS else WIN_Y


# ---------------------------------------------------------------- gameplay points
SPAWNS = {'SP_M1_Arrival': (76, WALK_Y), 'SP_M1_Office': (X(140), WALK_Y)}
HOTSPOTS = {
    # canonical (first slice)
    'plan_a': (X(322), WALK_Y),          # Konrad's drafting board
    'plan_b': (X(842), WALK_Y),          # flat-file drawer pulled out
    'overlay_table': (X(1178), WALK_Y),  # light table
    'emil': EMIL_POS,                    # Emil behind the counter
    'obs_window': (X(262), WALK_Y),      # Great Hall glimpse through the middle window
    'obs_photo': (X(204), WALK_Y),       # office photo on the covered drafting table
    'obs_notice': (X(1318), WALK_Y),     # typed list of 'relocated' tenants
    # exploration (TECHNICAL_ARCHITECTURE §12.2) -- arrival hall
    'exp_porter': (186, WALK_Y),         # porter's lodge hatch
    'exp_radio': (228, WALK_Y),          # radio with the glowing dial inside the lodge
    'exp_clock': (274, WALK_Y),          # regulator wall clock (working)
    'exp_pigeons': (338, WALK_Y),        # pigeons on the outside sill of the hall window
    'exp_photo': (430, WALK_Y),          # framed photos 'Chronik der Dienststelle'
    # library / reading room
    'exp_lib_shelf_1': (592, WALK_Y),
    'exp_lib_shelf_2': (668, WALK_Y),
    'exp_heater': (748, WALK_Y),         # radiator under the first library window (steam + knocking)
    'exp_card_catalogue': (815, WALK_Y),
    'exp_librarian_desk': (900, WALK_Y),
    'exp_globe': (GLOBE_X, WALK_Y),
    'exp_lib_shelf_3': (1020, WALK_Y),
    'exp_reading_table': (1100, WALK_Y),
    'exp_lib_shelf_4': (1176, WALK_Y),
    'exp_lib_shelf_5': (1232, WALK_Y),
    'exp_lib_hidden': (1284, WALK_Y),    # hidden: the right cupboard door of section V (swept arc on the floor)
    # office / archive / Emil (first-slice rooms)
    'exp_coat_stand': (X(107), WALK_Y),
    'exp_poster_aufbau': (X(476), WALK_Y),
    'exp_mouse': (X(920), WALK_Y),
    'exp_pneumatic_tube': (X(1070), WALK_Y),
    'exp_master_plan': (X(1462), WALK_Y),
}
# where the player should stand / what the prompt should point at (extension data)
FOCUS = {
    'plan_a': (X(322), 246), 'plan_b': (X(842), 262), 'overlay_table': (X(1178), 262), 'emil': (X(1412), 250),
    'obs_window': (X(262), 150), 'obs_photo': (X(206), 250), 'obs_notice': (X(1318), 214),
    'exp_porter': (190, 244), 'exp_radio': (220, 240), 'exp_clock': (274, 160), 'exp_pigeons': (338, 228),
    'exp_photo': (430, 186), 'exp_lib_shelf_1': (592, 150), 'exp_lib_shelf_2': (668, 150),
    'exp_heater': (742, 272), 'exp_card_catalogue': (815, 250), 'exp_librarian_desk': (900, 254),
    'exp_globe': (GLOBE_X, 256), 'exp_lib_shelf_3': (1020, 150), 'exp_reading_table': (1100, 264),
    'exp_lib_shelf_4': (1176, 150), 'exp_lib_shelf_5': (1232, 150), 'exp_lib_hidden': (1274, 274),
    'exp_coat_stand': (X(107), 240), 'exp_poster_aufbau': (X(476), 186), 'exp_mouse': (X(920), 284),
    'exp_pneumatic_tube': (X(1070), 214), 'exp_master_plan': (X(1414), 84),
}
FACING = {'obs_window': 'back', 'obs_notice': 'back', 'exp_clock': 'back', 'exp_pigeons': 'back',
          'exp_photo': 'back', 'exp_lib_shelf_1': 'back', 'exp_lib_shelf_2': 'back', 'exp_lib_shelf_3': 'back',
          'exp_lib_shelf_4': 'back', 'exp_lib_shelf_5': 'back', 'exp_poster_aufbau': 'back',
          'exp_master_plan': 'back', 'exp_pneumatic_tube': 'back'}
APPROACH = {k: ((v[0] if k in FACING else v[0] - 12, WALK_Y), FACING.get(k, 'right'))
            for k, v in HOTSPOTS.items()}
APPROACH.update({
    'plan_a': ((X(310), WALK_Y), 'right'), 'plan_b': ((X(826), WALK_Y), 'right'),
    'overlay_table': ((X(1160), WALK_Y), 'right'), 'emil': ((X(1376), WALK_Y), 'right'),
    'obs_photo': ((X(190), WALK_Y), 'right'),
})
NPCS = {
    'emil': {'pos': list(EMIL_POS), 'facing': 'left',
             'note': 'stands behind the counter prop (counter base_y 292 > feet y 284)'},
    'porter': {'pos': [190, 287], 'facing': 'left', 'hotspot': 'exp_porter', 'offset': [4, -13],
               'note': 'inside the porter\'s lodge, seen through its glazing (lodge prop base_y 293 > feet 287)'},
    'librarian': {'pos': [906, 284], 'facing': 'left', 'hotspot': 'exp_librarian_desk', 'offset': [6, -16],
                  'note': 'behind the librarian\'s desk (desk prop base_y 293 > feet 284)'},
}

# ---------------------------------------------------------------- parallax
PARALLAX = {'ext_sky': 0.05, 'ext_far': 0.10, 'ext_near': 0.18, 'fg_frame': 1.25}
TRAM_P = 0.20
TRAM_WIRE_Y = 211      # contact wire height (ext_near) = top of the pantograph
TRAM_ROOF_Y = 224      # roof line of the tram cars (world y)


def layer_width(p: float, margin: int = 16) -> int:
    """Required width for a parallax layer (TECHNICAL_ARCHITECTURE §3.1) + margin, rounded to 16."""
    w = VIEW_W + p * (WORLD_W - VIEW_W) + margin
    return int(-(-w // 16) * 16)


def local_x(world_x: float, p: float, cam_x: float) -> float:
    """parallax-layer local x seen at world x for a camera top-left cam_x"""
    return world_x - (1.0 - p) * cam_x


def cam_for(world_x: float) -> float:
    """typical gameplay camera top-left when the player stands at world_x"""
    return min(max(world_x - VIEW_W / 2, 0), WORLD_W - VIEW_W)
