import pygame
import sys
import random
from settings import *
from entities import Ball, Paddle, Brick, PowerUp
from levels import generate_level
from sound_manager import SoundManager
from save_manager import has_save, save_game, load_game, delete_save

_LIFE_LOST_DELAY   = 1800   # ms before resuming after a lost ball
_LEVEL_DONE_DELAY  = 2200   # ms before loading the next level
_IS_WEB = sys.platform == "emscripten"


class Game:
    # ─────────────────────────────────────────────── init ──────────────────
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            pass   # audio unavailable (WASM or missing driver)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock  = pygame.time.Clock()

        self.font_title  = pygame.font.SysFont("Arial", 54, bold=True)
        self.font_large  = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_small  = pygame.font.SysFont("Arial", 20)
        self.font_tiny   = pygame.font.SysFont("Arial", 13, bold=True)

        self.sound = SoundManager()

        # ── State machine ─────────────────────────────────────────────────
        # States: main_menu | options | playing | paused | pause_options
        #         life_lost | level_complete | game_over | victory
        self.state          = "main_menu"
        self.menu_selection = 0

        # ── Game data ─────────────────────────────────────────────────────
        self.level  = 1
        self.lives  = TOTAL_LIVES
        self.score  = 0

        self.paddle   = Paddle()
        self.balls    = []
        self.bricks   = []
        self.powerups = []

        self.speed_mult = 1.0
        self.fireball   = False

        self._transition_timer = 0
        self._notif            = ""
        self._notif_timer      = 0

        # ── Touch / mouse control ─────────────────────────────────────────
        self._touch_active = False   # True while finger/mouse button is held
        self._touch_x      = WIDTH // 2

    # ─────────────────────────────────────────────── main loop ─────────────
    def run_frame(self):
        """Execute one frame (called by the asyncio loop in main.py)."""
        dt = self.clock.tick(FPS)
        self._handle_events(dt)
        self._update(dt)
        self._draw()
        pygame.display.flip()

    def run(self):
        """Blocking loop — kept for direct desktop launches."""
        while True:
            self.run_frame()

    # ─────────────────────────────────────────────── events ────────────────
    def _handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            # ── Keyboard ──────────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                k = event.key

                if self.state == "main_menu":
                    self._nav(k, self._main_menu_items(), self._main_menu_action)

                elif self.state == "options":
                    self._nav(k, self._options_items(), self._options_action,
                              back="main_menu")

                elif self.state == "playing":
                    if k == pygame.K_ESCAPE:
                        self.state          = "paused"
                        self.menu_selection = 0
                    elif k == pygame.K_SPACE:
                        for b in self.balls:
                            if not b.launched:
                                b.launched = True

                elif self.state == "paused":
                    if k == pygame.K_ESCAPE:
                        self.state = "playing"
                    else:
                        self._nav(k, self._pause_items(), self._pause_action)

                elif self.state == "pause_options":
                    self._nav(k, self._options_items(), self._pause_options_action,
                              back="paused")

                elif self.state in ("game_over", "victory"):
                    if k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                        self.state          = "main_menu"
                        self.menu_selection = 0

            # ── Touch / Mouse ──────────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.state in ("main_menu", "options", "paused", "pause_options"):
                    self._handle_menu_tap(pos)
                elif self.state == "playing":
                    self._touch_active = True
                    self._touch_x      = pos[0]
                    for b in self.balls:
                        if not b.launched:
                            b.launched = True
                elif self.state in ("game_over", "victory"):
                    self.state          = "main_menu"
                    self.menu_selection = 0

            elif event.type == pygame.MOUSEBUTTONUP:
                self._touch_active = False

            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:   # finger/button still held
                    if self.state == "playing":
                        self._touch_active = True
                        self._touch_x      = event.pos[0]

    def _nav(self, key, items, action_fn, back=None):
        """Generic keyboard navigation for menus."""
        if key == pygame.K_UP:
            self.menu_selection = (self.menu_selection - 1) % len(items)
            self.sound.play("menu_move")
        elif key == pygame.K_DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(items)
            self.sound.play("menu_move")
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self.sound.play("menu_select")
            action_fn(self.menu_selection)
        elif key == pygame.K_ESCAPE and back:
            self.state          = back
            self.menu_selection = 0

    def _handle_menu_tap(self, pos):
        """Select and activate the menu item closest to the tap position."""
        if self.state == "main_menu":
            items     = self._main_menu_items()
            action_fn = self._main_menu_action
        elif self.state == "options":
            items     = self._options_items()
            action_fn = self._options_action
        elif self.state == "paused":
            items     = self._pause_items()
            action_fn = self._pause_action
        elif self.state == "pause_options":
            items     = self._options_items()
            action_fn = self._pause_options_action
        else:
            return

        for i in range(len(items)):
            item_cy = 250 + i * 62
            if abs(pos[1] - item_cy) < 35:
                self.menu_selection = i
                self.sound.play("menu_select")
                action_fn(i)
                return

    # ─────────────────────────────────────────────── menu data ─────────────
    def _main_menu_items(self):
        items = ["Nouvelle Partie"]
        if has_save():
            items.append("Continuer")
        items.append("Options")
        if not _IS_WEB:
            items.append("Quitter")
        return items

    def _main_menu_action(self, idx):
        choice = self._main_menu_items()[idx]
        if choice == "Nouvelle Partie":
            self._start_new_game()
        elif choice == "Continuer":
            self._load_and_continue()
        elif choice == "Options":
            self.state          = "options"
            self.menu_selection = 0
        elif choice == "Quitter":
            self._quit()

    def _options_items(self):
        return [f"Son : {'ON' if self.sound.enabled else 'OFF'}", "Retour"]

    def _options_action(self, idx):
        choice = self._options_items()[idx]
        if "Son" in choice:
            self.sound.toggle()
        elif choice == "Retour":
            self.state          = "main_menu"
            self.menu_selection = 0

    def _pause_items(self):
        items = ["Reprendre", "Options", "Menu Principal"]
        if not _IS_WEB:
            items.append("Quitter")
        return items

    def _pause_action(self, idx):
        choice = self._pause_items()[idx]
        if choice == "Reprendre":
            self.state = "playing"
        elif choice == "Options":
            self.state          = "pause_options"
            self.menu_selection = 0
        elif choice == "Menu Principal":
            self.state          = "main_menu"
            self.menu_selection = 0
        elif choice == "Quitter":
            self._quit()

    def _pause_options_action(self, idx):
        choice = self._options_items()[idx]
        if "Son" in choice:
            self.sound.toggle()
        elif choice == "Retour":
            self.state          = "paused"
            self.menu_selection = 0

    # ─────────────────────────────────────────────── update ────────────────
    def _update(self, dt):
        if self.state == "playing":
            self._update_game()

        elif self.state == "life_lost":
            self._transition_timer -= dt
            if self._transition_timer <= 0:
                if self.lives > 0:
                    self._reset_ball()
                    self.state = "playing"
                else:
                    self.sound.play("game_over")
                    delete_save()
                    self.state = "game_over"

        elif self.state == "level_complete":
            self._transition_timer -= dt
            if self._transition_timer <= 0:
                self.level += 1
                if self.level > NUM_LEVELS:
                    self.sound.play("victory")
                    delete_save()
                    self.state = "victory"
                else:
                    self._start_level()
                    self.state = "playing"

        # notification timer
        if self._notif_timer > 0:
            self._notif_timer -= dt
        if self._notif_timer <= 0:
            self._notif = ""

    def _update_game(self):
        keys = pygame.key.get_pressed()
        self.paddle.move(keys)

        # Touch/mouse: drag to position paddle
        if self._touch_active:
            target_x = self._touch_x - self.paddle.width // 2
            self.paddle.x = max(0, min(WIDTH - self.paddle.width, target_x))

        # ── Move balls & collect wall/paddle/lost events ─────────────────
        lost_balls = []
        for ball in self.balls:
            ev = ball.update(self.paddle)
            if ev == "wall":
                self.sound.play("wall")
            elif ev == "paddle":
                self.sound.play("paddle")
            elif ev == "lost":
                lost_balls.append(ball)
        for b in lost_balls:
            self.balls.remove(b)

        if not self.balls:
            self.lives -= 1
            self.sound.play("life_lost")
            self._transition_timer = _LIFE_LOST_DELAY
            self.state = "life_lost"
            return

        # ── Ball-brick collisions ─────────────────────────────────────────
        for ball in self.balls:
            already_hit = set()
            for brick in self.bricks:
                if not brick.alive or id(brick) in already_hit:
                    continue
                if ball.check_brick_collision(brick):
                    already_hit.add(id(brick))
                    destroyed = brick.hit(ball.fireball)
                    if destroyed:
                        self.score += brick.max_hits * 10
                        self.sound.play("brick")
                        self._maybe_drop_powerup(brick)
                    else:
                        self.sound.play("brick_hit")

        self.bricks = [b for b in self.bricks if b.alive]

        # ── Level complete? ───────────────────────────────────────────────
        if not self.bricks:
            next_lvl = self.level + 1
            if next_lvl <= NUM_LEVELS:
                save_game(next_lvl, self.lives)
            else:
                delete_save()
            self.sound.play("level_complete")
            self._transition_timer = _LEVEL_DONE_DELAY
            self.state = "level_complete"
            return

        # ── PowerUps ─────────────────────────────────────────────────────
        dead = []
        for pu in self.powerups:
            pu.update()
            if not pu.alive:
                dead.append(pu)
                continue
            if pu.collides_paddle(self.paddle):
                self._apply_powerup(pu)
                dead.append(pu)
        for pu in dead:
            self.powerups.remove(pu)

    # ─────────────────────────────────────────────── game setup ────────────
    def _start_new_game(self):
        self.level = 1
        self.lives = TOTAL_LIVES
        self.score = 0
        delete_save()
        self._start_level()
        self.state = "playing"

    def _load_and_continue(self):
        data = load_game()
        if data is None:
            self._start_new_game()
            return
        self.level, self.lives = data
        self.score = 0
        self._start_level()
        self.state = "playing"

    def _start_level(self):
        self.paddle   = Paddle()
        self.balls    = [Ball()]
        self.powerups = []
        self.speed_mult = 1.0
        self.fireball   = False
        self.bricks = [
            Brick(col, row, hits)
            for col, row, hits in generate_level(self.level)
        ]
        self._show_notif(f"Niveau {self.level}", 2000)

    def _reset_ball(self):
        """After life lost: keep bricks, reset paddle/ball/effects."""
        self.paddle     = Paddle()
        self.balls      = [Ball()]
        self.powerups   = []
        self.speed_mult = 1.0
        self.fireball   = False

    # ─────────────────────────────────────────────── power-ups ─────────────
    def _maybe_drop_powerup(self, brick):
        if random.random() < POWERUP_CHANCE:
            pu_type = random.choice([
                PU_EXPAND, PU_SHRINK, PU_MULTIBALL,
                PU_SLOW, PU_FAST, PU_LIFE, PU_FIREBALL,
            ])
            cx = brick.x + BRICK_WIDTH  // 2
            cy = brick.y + BRICK_HEIGHT // 2
            self.powerups.append(PowerUp(cx, cy, pu_type))

    def _apply_powerup(self, pu):
        self.sound.play("powerup")
        self._show_notif(POWERUP_DESCS.get(pu.type, ""), 1600)

        if pu.type == PU_EXPAND:
            self.paddle.expand()

        elif pu.type == PU_SHRINK:
            self.paddle.shrink()

        elif pu.type == PU_MULTIBALL:
            new_balls = []
            for ball in self.balls:
                if ball.launched:
                    new_balls.append(ball.clone(-25))
                    new_balls.append(ball.clone(+25))
            self.balls.extend(new_balls)

        elif pu.type == PU_SLOW:
            self.speed_mult = 0.6
            for b in self.balls:
                b.set_speed(BALL_BASE_SPEED * self.speed_mult)

        elif pu.type == PU_FAST:
            self.speed_mult = 1.5
            for b in self.balls:
                b.set_speed(BALL_BASE_SPEED * self.speed_mult)

        elif pu.type == PU_LIFE:
            self.lives += 1

        elif pu.type == PU_FIREBALL:
            self.fireball = True
            for b in self.balls:
                b.fireball = True

    # ─────────────────────────────────────────────── notifications ──────────
    def _show_notif(self, text, duration_ms):
        self._notif       = text
        self._notif_timer = duration_ms

    # ─────────────────────────────────────────────── drawing ───────────────
    def _draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == "main_menu":
            self._draw_menu("CASSE-BRIQUE", self._main_menu_items(), self.menu_selection)

        elif self.state == "options":
            self._draw_menu("OPTIONS", self._options_items(), self.menu_selection)

        elif self.state in ("playing", "life_lost", "level_complete"):
            self._draw_game()
            if self.state == "life_lost":
                msg = (f"Vie perdue !  ({self.lives} vie{'s' if self.lives > 1 else ''} restante{'s' if self.lives > 1 else ''})"
                       if self.lives > 0 else "Vie perdue !")
                self._draw_overlay(msg, RED)
            elif self.state == "level_complete":
                self._draw_overlay(f"Niveau {self.level} terminé !", GREEN)

        elif self.state == "paused":
            self._draw_game()
            self._draw_pause_overlay()

        elif self.state == "pause_options":
            self._draw_game()
            self._draw_menu("OPTIONS", self._options_items(), self.menu_selection,
                            with_overlay=True)

        elif self.state == "game_over":
            self._draw_end_screen("GAME OVER", RED,
                                  f"Score final : {self.score}",
                                  "Appuyez sur une touche pour revenir au menu")

        elif self.state == "victory":
            self._draw_end_screen("VICTOIRE !", YELLOW,
                                  f"Score final : {self.score}",
                                  "Félicitations — 10 niveaux complétés !",
                                  extra="Appuyez sur une touche pour revenir au menu")

    # ── Sub-drawers ─────────────────────────────────────────────────────────
    def _draw_game(self):
        for brick in self.bricks:
            brick.draw(self.screen)
        for pu in self.powerups:
            pu.draw(self.screen, self.font_tiny)
        self.paddle.draw(self.screen)
        for ball in self.balls:
            ball.draw(self.screen)
        self._draw_hud()

        # Notification
        if self._notif and self._notif_timer > 0:
            alpha = min(255, int(255 * min(1.0, self._notif_timer / 400)))
            surf  = self.font_medium.render(self._notif, True, YELLOW)
            surf.set_alpha(alpha)
            self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT - 75)))

        # Launch hint (keyboard or touch)
        if any(not b.launched for b in self.balls):
            hint_text = "Touchez l'écran pour lancer" if _IS_WEB else "ESPACE pour lancer"
            hint = self.font_small.render(hint_text, True, GRAY)
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, PADDLE_Y - 30)))

    def _draw_hud(self):
        # Level
        lvl = self.font_small.render(f"Niveau {self.level}/{NUM_LEVELS}", True, WHITE)
        self.screen.blit(lvl, (10, 10))

        # Score (centered)
        sc = self.font_small.render(f"Score : {self.score}", True, WHITE)
        self.screen.blit(sc, sc.get_rect(centerx=WIDTH // 2, y=10))

        # Lives (hearts on the right)
        hx = WIDTH - 10
        for _ in range(self.lives):
            h = self.font_small.render("♥", True, RED)
            hx -= h.get_width() + 3
            self.screen.blit(h, (hx, 10))

        # Active effects
        effects = []
        if self.speed_mult < 1.0:
            effects.append(("[Lent]",    CYAN))
        elif self.speed_mult > 1.0:
            effects.append(("[Rapide]",  ORANGE))
        if self.fireball:
            effects.append(("[Fireball]", (255, 120, 20)))

        ex = 10
        for label, color in effects:
            et = self.font_tiny.render(label, True, color)
            self.screen.blit(et, (ex, HEIGHT - 18))
            ex += et.get_width() + 8

    def _draw_menu(self, title, items, selected, with_overlay=False):
        if with_overlay:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 165))
            self.screen.blit(ov, (0, 0))

        # Title
        t = self.font_title.render(title, True, WHITE)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, 130)))

        # Items
        for i, item in enumerate(items):
            color = YELLOW if i == selected else LIGHT_GRAY
            txt   = self.font_medium.render(item, True, color)
            y     = 250 + i * 62
            r     = txt.get_rect(center=(WIDTH // 2, y))
            if i == selected:
                bg = pygame.Rect(r.left - 22, r.top - 7, r.width + 44, r.height + 14)
                pygame.draw.rect(self.screen, PANEL_COLOR, bg, border_radius=8)
                pygame.draw.rect(self.screen, YELLOW, bg, 2, border_radius=8)
            self.screen.blit(txt, r)

        # Touch hint on web
        if _IS_WEB:
            hint = self.font_tiny.render("Touchez un élément pour le sélectionner", True, GRAY)
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 20)))

    def _draw_pause_overlay(self):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        self.screen.blit(ov, (0, 0))
        self._draw_menu("PAUSE", self._pause_items(), self.menu_selection)

    def _draw_overlay(self, message, color):
        ov = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        self.screen.blit(ov, (0, HEIGHT // 2 - 45))
        txt = self.font_large.render(message, True, color)
        self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    def _draw_end_screen(self, title, title_color, subtitle, line1, extra=None):
        t1 = self.font_title.render(title,    True, title_color)
        t2 = self.font_medium.render(subtitle, True, WHITE)
        t3 = self.font_small.render(line1,    True, GREEN if extra else GRAY)
        self.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)))
        self.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        self.screen.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
        if extra:
            t4 = self.font_small.render(extra, True, GRAY)
            self.screen.blit(t4, t4.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 85)))

    # ─────────────────────────────────────────────── misc ──────────────────
    def _quit(self):
        if _IS_WEB:
            # No meaningful quit in a browser — return to main menu
            self.state          = "main_menu"
            self.menu_selection = 0
            return
        pygame.quit()
        sys.exit()
