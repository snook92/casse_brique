import json
import os
import sys
from settings import TOTAL_LIVES

_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")
_IS_WEB = sys.platform == "emscripten"
_mem_save: dict = {}   # in-memory fallback when running in WASM


def has_save():
    if _IS_WEB:
        return bool(_mem_save)
    return os.path.exists(_SAVE_PATH)


def save_game(level: int, lives: int) -> bool:
    if _IS_WEB:
        _mem_save.update({"level": level, "lives": lives})
        return True
    try:
        with open(_SAVE_PATH, "w") as f:
            json.dump({"level": level, "lives": lives}, f)
        return True
    except OSError as e:
        print(f"[Save] Erreur : {e}")
        return False


def load_game():
    """Returns (level, lives) or None if no save."""
    if _IS_WEB:
        if not _mem_save:
            return None
        return int(_mem_save.get("level", 1)), int(_mem_save.get("lives", TOTAL_LIVES))
    if not has_save():
        return None
    try:
        with open(_SAVE_PATH) as f:
            data = json.load(f)
        return int(data.get("level", 1)), int(data.get("lives", TOTAL_LIVES))
    except (OSError, ValueError, KeyError):
        return None


def delete_save():
    if _IS_WEB:
        _mem_save.clear()
        return
    if os.path.exists(_SAVE_PATH):
        os.remove(_SAVE_PATH)
