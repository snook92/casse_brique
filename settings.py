WINDOW_TITLE = "Casse-Brique"
WIDTH        = 800
HEIGHT       = 600
FPS          = 60

# ── Colors ──────────────────────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = (110, 110, 130)
DARK_GRAY  = (40,  40,  60)
LIGHT_GRAY = (180, 180, 200)
RED        = (220, 50,  50)
GREEN      = (50,  200, 100)
BLUE       = (50,  120, 220)
CYAN       = (50,  200, 220)
YELLOW     = (230, 210, 50)
ORANGE     = (230, 140, 50)
MAGENTA    = (200, 50,  200)
PINK       = (230, 100, 160)

BG_COLOR    = (12,  12,  28)
PANEL_COLOR = (30,  30,  55)

# ── Game ─────────────────────────────────────────────────────────────────────
TOTAL_LIVES = 5
NUM_LEVELS  = 10

# ── Paddle ───────────────────────────────────────────────────────────────────
PADDLE_WIDTH_DEFAULT = 100
PADDLE_HEIGHT        = 14
PADDLE_SPEED         = 8
PADDLE_Y             = HEIGHT - 50
PADDLE_MIN_WIDTH     = 50
PADDLE_MAX_WIDTH     = 200
PADDLE_COLOR         = (100, 180, 255)

# ── Ball ─────────────────────────────────────────────────────────────────────
BALL_RADIUS     = 8
BALL_BASE_SPEED = 5.5

# ── Bricks ───────────────────────────────────────────────────────────────────
BRICK_COLS      = 11
BRICK_WIDTH     = 60
BRICK_HEIGHT    = 22
BRICK_PADDING_X = 5
BRICK_PADDING_Y = 4
BRICK_TOP_OFFSET = 100

# Color by remaining hit points
BRICK_COLORS = {
    1: (70,  185, 90),   # green
    2: (200, 150, 50),   # orange
    3: (210, 55,  55),   # red
}

# ── Power-ups ────────────────────────────────────────────────────────────────
POWERUP_SIZE   = 22
POWERUP_SPEED  = 2.5
POWERUP_CHANCE = 0.20   # probability per destroyed brick

PU_EXPAND    = "expand"
PU_SHRINK    = "shrink"
PU_MULTIBALL = "multiball"
PU_SLOW      = "slow"
PU_FAST      = "fast"
PU_LIFE      = "life"
PU_FIREBALL  = "fireball"

POWERUP_COLORS = {
    PU_EXPAND:    (50,  220, 100),
    PU_SHRINK:    (220, 70,  70),
    PU_MULTIBALL: (230, 220, 50),
    PU_SLOW:      (50,  210, 230),
    PU_FAST:      (230, 155, 50),
    PU_LIFE:      (230, 70,  200),
    PU_FIREBALL:  (255, 110, 20),
}

POWERUP_LABELS = {
    PU_EXPAND:    "+",
    PU_SHRINK:    "-",
    PU_MULTIBALL: "x3",
    PU_SLOW:      "<<",
    PU_FAST:      ">>",
    PU_LIFE:      "+1",
    PU_FIREBALL:  "FB",
}

POWERUP_DESCS = {
    PU_EXPAND:    "Raquette agrandie !",
    PU_SHRINK:    "Raquette réduite...",
    PU_MULTIBALL: "Multi-balles !",
    PU_SLOW:      "Balle ralentie",
    PU_FAST:      "Balle accélérée !",
    PU_LIFE:      "Vie bonus !",
    PU_FIREBALL:  "Boule de Feu !",
}

SOUND_SAMPLE_RATE = 44100
