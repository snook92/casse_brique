from settings import BRICK_COLS


def generate_level(level_num):
    """Return list of (col, row, hits) for the given level (1-10).

    Each entry in rows_config is the hit-point value for that row (top to bottom).
    Levels grow harder by adding more rows and tougher bricks.
    """
    configs = {
        1:  [1, 1, 1],
        2:  [1, 1, 1, 1],
        3:  [2, 1, 1, 1],
        4:  [2, 2, 1, 1, 1],
        5:  [3, 2, 2, 1, 1],
        6:  [3, 3, 2, 2, 1, 1],
        7:  [3, 3, 3, 2, 2, 1],
        8:  [3, 3, 3, 2, 2, 2, 1],
        9:  [3, 3, 3, 3, 2, 2, 2],
        10: [3, 3, 3, 3, 3, 2, 2, 2],
    }
    rows = configs.get(level_num, [1, 1, 1])
    return [
        (col, row_idx, hits)
        for row_idx, hits in enumerate(rows)
        for col in range(BRICK_COLS)
    ]
