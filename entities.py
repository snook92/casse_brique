import pygame
import math
import random
from settings import *


class Paddle:
    def __init__(self):
        self.width  = PADDLE_WIDTH_DEFAULT
        self.height = PADDLE_HEIGHT
        self.x      = (WIDTH - self.width) // 2
        self.y      = PADDLE_Y
        self.color  = PADDLE_COLOR

    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT]:
            self.x += PADDLE_SPEED
        self.x = max(0, min(WIDTH - self.width, self.x))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def expand(self, amount=35):
        cx = self.x + self.width // 2
        self.width = min(PADDLE_MAX_WIDTH, self.width + amount)
        self.x = max(0, min(WIDTH - self.width, cx - self.width // 2))

    def shrink(self, amount=28):
        cx = self.x + self.width // 2
        self.width = max(PADDLE_MIN_WIDTH, self.width - amount)
        self.x = max(0, min(WIDTH - self.width, cx - self.width // 2))

    def reset_size(self):
        cx = self.x + self.width // 2
        self.width = PADDLE_WIDTH_DEFAULT
        self.x = max(0, min(WIDTH - self.width, cx - self.width // 2))

    def draw(self, surface):
        rect = self.get_rect()
        pygame.draw.rect(surface, self.color, rect, border_radius=6)
        # Top highlight
        hi = pygame.Rect(rect.x + 3, rect.y + 2, rect.width - 6, 4)
        pygame.draw.rect(surface, (180, 220, 255), hi, border_radius=4)


class Ball:
    def __init__(self, x=None, y=None, vx=None, vy=None):
        self.x = float(x if x is not None else WIDTH // 2)
        self.y = float(y if y is not None else PADDLE_Y - BALL_RADIUS - 2)
        if vx is None or vy is None:
            ang = math.radians(random.uniform(-40, 40))
            self.vx = BALL_BASE_SPEED * math.sin(ang)
            self.vy = -BALL_BASE_SPEED * math.cos(ang)
        else:
            self.vx = float(vx)
            self.vy = float(vy)
        self.radius   = BALL_RADIUS
        self.launched = False
        self.fireball = False

    @property
    def speed(self):
        return math.sqrt(self.vx ** 2 + self.vy ** 2)

    def set_speed(self, s):
        cur = self.speed
        if cur > 0:
            self.vx = self.vx / cur * s
            self.vy = self.vy / cur * s

    def update(self, paddle):
        """Move ball and resolve wall + paddle collisions.
        Returns an event string ('wall', 'paddle', 'lost') or None."""
        if not self.launched:
            self.x = paddle.x + paddle.width / 2.0
            self.y = float(PADDLE_Y - BALL_RADIUS - 2)
            return None

        self.x += self.vx
        self.y += self.vy

        event = None

        # Side walls
        if self.x - self.radius <= 0:
            self.x = float(self.radius)
            self.vx = abs(self.vx)
            event = "wall"
        elif self.x + self.radius >= WIDTH:
            self.x = float(WIDTH - self.radius)
            self.vx = -abs(self.vx)
            event = "wall"

        # Top wall
        if self.y - self.radius <= 0:
            self.y = float(self.radius)
            self.vy = abs(self.vy)
            event = "wall"

        # Paddle
        prect = paddle.get_rect()
        if (self.vy > 0
                and self.y + self.radius >= prect.top
                and self.y - self.radius <= prect.bottom
                and self.x + self.radius > prect.left
                and self.x - self.radius < prect.right):
            hit_pos = (self.x - prect.left) / prect.width   # 0..1
            angle   = math.radians((hit_pos - 0.5) * 130)   # −65°..+65°
            s = self.speed
            self.vx = s * math.sin(angle)
            self.vy = -abs(s * math.cos(angle))
            self.y  = float(prect.top - self.radius)
            event = "paddle"

        # Out of bounds (bottom)
        if self.y - self.radius > HEIGHT:
            return "lost"

        return event

    def check_brick_collision(self, brick):
        """Returns True and applies bounce if ball touches this brick."""
        if not self.launched:
            return False
        brect = brick.get_rect()
        # Closest point on rect to ball center
        cx = max(brect.left, min(self.x, brect.right))
        cy = max(brect.top,  min(self.y, brect.bottom))
        dx = self.x - cx
        dy = self.y - cy
        if dx * dx + dy * dy > self.radius * self.radius:
            return False
        # Bounce direction via penetration depth
        if not self.fireball:
            ov_x = (brect.width  / 2 + self.radius) - abs(self.x - brect.centerx)
            ov_y = (brect.height / 2 + self.radius) - abs(self.y - brect.centery)
            if ov_x < ov_y:
                self.vx = math.copysign(abs(self.vx), self.x - brect.centerx)
            else:
                self.vy = math.copysign(abs(self.vy), self.y - brect.centery)
        return True

    def clone(self, angle_offset):
        """Return a copy of this ball with direction rotated by angle_offset degrees."""
        cur = math.degrees(math.atan2(self.vx, -self.vy))
        rad = math.radians(cur + angle_offset)
        s   = self.speed
        b   = Ball(self.x, self.y, s * math.sin(rad), -s * math.cos(rad))
        b.launched  = True
        b.fireball  = self.fireball
        return b

    def draw(self, surface):
        color = (255, 120, 10) if self.fireball else WHITE
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        if self.fireball:
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius - 3)
        else:
            pygame.draw.circle(surface, (200, 230, 255),
                               (int(self.x) - 2, int(self.y) - 2), 3)


class Brick:
    def __init__(self, col, row, hits=1):
        self.hits     = hits
        self.max_hits = hits
        self.alive    = True
        total_w = BRICK_COLS * (BRICK_WIDTH + BRICK_PADDING_X) - BRICK_PADDING_X
        ox = (WIDTH - total_w) // 2
        self.x = ox + col * (BRICK_WIDTH + BRICK_PADDING_X)
        self.y = BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_PADDING_Y)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BRICK_WIDTH, BRICK_HEIGHT)

    def hit(self, fireball=False):
        """Returns True if the brick is destroyed."""
        self.hits = 0 if fireball else self.hits - 1
        if self.hits <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        color = BRICK_COLORS.get(self.hits, BRICK_COLORS[3])
        rect  = self.get_rect()
        pygame.draw.rect(surface, color, rect, border_radius=3)
        # Light top edge
        hi = (min(color[0] + 70, 255), min(color[1] + 70, 255), min(color[2] + 70, 255))
        pygame.draw.line(surface, hi, (rect.x + 2, rect.y + 1), (rect.right - 3, rect.y + 1))
        # Dark bottom edge
        sh = (max(color[0] - 60, 0), max(color[1] - 60, 0), max(color[2] - 60, 0))
        pygame.draw.line(surface, sh, (rect.x + 2, rect.bottom - 2), (rect.right - 3, rect.bottom - 2))


class PowerUp:
    def __init__(self, x, y, pu_type):
        self.x     = float(x)
        self.y     = float(y)
        self.type  = pu_type
        self.alive = True
        self.color = POWERUP_COLORS.get(pu_type, WHITE)
        self.label = POWERUP_LABELS.get(pu_type, "?")

    def update(self):
        self.y += POWERUP_SPEED
        if self.y > HEIGHT + POWERUP_SIZE:
            self.alive = False

    def get_rect(self):
        s = POWERUP_SIZE
        return pygame.Rect(int(self.x) - s // 2, int(self.y) - s // 2, s, s)

    def collides_paddle(self, paddle):
        return self.get_rect().colliderect(paddle.get_rect())

    def draw(self, surface, tiny_font):
        rect = self.get_rect()
        pygame.draw.rect(surface, self.color, rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, rect, 1, border_radius=4)
        txt = tiny_font.render(self.label, True, BLACK)
        surface.blit(txt, txt.get_rect(center=rect.center))
