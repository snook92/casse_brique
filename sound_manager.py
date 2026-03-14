import pygame
import array
import math

_RATE = 44100


def _tone(freq, duration, volume=0.35, fade=True):
    n   = int(_RATE * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / _RATE
        s = math.sin(2 * math.pi * freq * t)
        if fade:
            s *= 1.0 - i / n
        v = max(-32768, min(32767, int(volume * 32767 * s)))
        buf.append(v)
        buf.append(v)   # stereo
    return pygame.mixer.Sound(buffer=buf)


def _chord(freqs, duration, volume=0.28, fade=True):
    n   = int(_RATE * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / _RATE
        s = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        if fade:
            s *= 1.0 - i / n
        v = max(-32768, min(32767, int(volume * 32767 * s)))
        buf.append(v)
        buf.append(v)
    return pygame.mixer.Sound(buffer=buf)


class SoundManager:
    def __init__(self):
        self.enabled = True
        self._sounds = {}
        self._load()

    def _load(self):
        try:
            self._sounds = {
                "wall":           _tone(320,  0.05, 0.25),
                "paddle":         _tone(440,  0.07, 0.35),
                "brick":          _tone(640,  0.06, 0.30),
                "brick_hit":      _chord([400, 510], 0.07, 0.28),
                "powerup":        _chord([523, 659, 784], 0.28, 0.36),
                "life_lost":      _tone(170,  0.55, 0.40),
                "level_complete": _chord([523, 659, 784, 1047], 0.55, 0.38),
                "game_over":      _tone(120,  0.80, 0.40),
                "victory":        _chord([523, 659, 784, 1047, 1318], 0.75, 0.38),
                "menu_move":      _tone(500,  0.04, 0.18),
                "menu_select":    _chord([440, 550], 0.11, 0.30),
            }
        except Exception as e:
            print(f"[Sound] Initialisation impossible : {e}")
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self._sounds:
            self._sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
