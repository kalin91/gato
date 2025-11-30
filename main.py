import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Gato Interactivo")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
PINK = (255, 192, 203)

# Global state
background_color = (30, 30, 30)
background_shapes = []
show_meow = 0
ball_pos = None

class Cat:
    def __init__(self, x, y, scale=1.0):
        self.x = x
        self.y = y
        self.scale = scale
        self.original_y = y
        self.y_velocity = 0
        self.is_jumping = False
        self.paw_angle = 0
        self.paw_direction = 1
        self.is_waving = False
        self.tail_angle = 0
        self.tail_speed = 0.05
        self.eye_offset_x = 0
        self.eye_offset_y = 0
        self.target_x = x
        self.blink_timer = 0
        self.is_blinking = False
        self.mouth_state = 'normal'
        self.mouth_timer = 0

    def update(self):
        # Jumping logic
        if self.is_jumping:
            self.y += self.y_velocity
            self.y_velocity += 1  # Gravity
            if self.y >= self.original_y:
                self.y = self.original_y
                self.is_jumping = False
                self.y_velocity = 0

        # Blinking logic
        self.blink_timer += 1
        if self.blink_timer > 180:  # Blink every ~3 seconds
            self.is_blinking = True
            if self.blink_timer > 190:
                self.is_blinking = False
                self.blink_timer = 0

        # Mouth timer
        if self.mouth_timer > 0:
            self.mouth_timer -= 1
        else:
            self.mouth_state = 'normal'

        # Waving logic
        if self.is_waving:
            self.paw_angle += 5 * self.paw_direction
            if self.paw_angle > 45 or self.paw_angle < -10:
                self.paw_direction *= -1
        else:
            # Return paw to neutral
            if self.paw_angle > 0:
                self.paw_angle -= 5
            elif self.paw_angle < 0:
                self.paw_angle += 5

        # Tail wagging
        self.tail_angle += self.tail_speed
        
        # Movement (chasing ball)
        if self.x < self.target_x:
            self.x += 5
        elif self.x > self.target_x:
            self.x -= 5

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = -20

    def open_mouth(self):
        self.mouth_state = 'open'
        self.mouth_timer = 60

    def stick_tongue_out(self):
        self.mouth_state = 'tongue'
        self.mouth_timer = 60

    def wave(self):
        self.is_waving = True

    def stop_wave(self):
        self.is_waving = False

    def look_at(self, target_x, target_y):
        # Simple eye movement
        dx = target_x - self.x
        dy = target_y - self.y
        self.eye_offset_x = max(-5, min(5, dx / 50))
        self.eye_offset_y = max(-5, min(5, dy / 50))

    def draw(self, surface):
        # Helper for scaling
        def s(val): return int(val * self.scale)
        
        cx, cy = int(self.x), int(self.y)

        # Tail
        # slight jitter
        tail_end_x = cx + s(120) + s(30) * random.choice([-1, 1]) * 0.1
        tail_end_y = cy - s(50) + s(20) * random.choice([-1, 1]) * 0.1
        pygame.draw.line(
            surface, GRAY, (cx + s(80), cy + s(50)),
            (tail_end_x, tail_end_y), s(15)
        )

        # Body
        pygame.draw.ellipse(surface, GRAY, (cx - s(100), cy, s(200), s(150)))

        # Head (Moved down to connect with body)
        head_y = cy - s(60)
        pygame.draw.circle(surface, GRAY, (cx, head_y), s(70))

        # Ears
        pygame.draw.polygon(surface, GRAY, [
            (cx - s(60), head_y - s(20)),
            (cx - s(20), head_y - s(50)),
            (cx - s(70), head_y - s(90))
        ])
        pygame.draw.polygon(surface, GRAY, [
            (cx + s(60), head_y - s(20)),
            (cx + s(20), head_y - s(50)),
            (cx + s(70), head_y - s(90))
        ])

        # Inner Ears
        pygame.draw.polygon(surface, PINK, [
            (cx - s(55), head_y - s(25)),
            (cx - s(25), head_y - s(50)),
            (cx - s(65), head_y - s(80))
        ])
        pygame.draw.polygon(surface, PINK, [
            (cx + s(55), head_y - s(25)),
            (cx + s(25), head_y - s(50)),
            (cx + s(65), head_y - s(80))
        ])

        # Eyes
        eye_y = head_y - s(10)
        if self.is_blinking:
            pygame.draw.line(
                surface, BLACK, (cx - s(40), eye_y), (cx - s(10), eye_y), s(2)
            )
            pygame.draw.line(
                surface, BLACK, (cx + s(10), eye_y), (cx + s(40), eye_y), s(2)
            )
        else:
            pygame.draw.circle(surface, WHITE, (cx - s(25), eye_y), s(15))
            pygame.draw.circle(surface, WHITE, (cx + s(25), eye_y), s(15))

            # Pupils
            pygame.draw.circle(
                surface, BLACK,
                (
                    cx - s(25) + int(self.eye_offset_x),
                    eye_y + int(self.eye_offset_y)
                ),
                s(7)
            )
            pygame.draw.circle(
                surface, BLACK,
                (
                    cx + s(25) + int(self.eye_offset_x),
                    eye_y + int(self.eye_offset_y)
                ),
                s(7)
            )

        # Nose
        pygame.draw.circle(surface, PINK, (cx, head_y + s(15)), s(8))

        # Mouth
        mouth_y = head_y + s(35)
        if self.mouth_state == 'open':
            pygame.draw.circle(surface, BLACK, (cx, mouth_y), s(10))
        elif self.mouth_state == 'tongue':
            pygame.draw.circle(surface, BLACK, (cx, mouth_y), s(10))
            pygame.draw.ellipse(
                surface, PINK, (cx - s(5), mouth_y, s(10), s(15))
            )
        else:
            pygame.draw.arc(
                surface, BLACK,
                (cx - s(10), mouth_y - s(10), s(10), s(10)),
                3.14, 0, s(2)
            )
            pygame.draw.arc(
                surface, BLACK,
                (cx, mouth_y - s(10), s(10), s(10)),
                3.14, 0, s(2)
            )

        # Whiskers
        for i in range(3):
            pygame.draw.line(
                surface, BLACK,
                (cx - s(10), head_y + s(25) + i*s(5)),
                (cx - s(60), head_y + s(15) + i*s(10)),
                s(2)
            )
            pygame.draw.line(
                surface, BLACK,
                (cx + s(10), head_y + s(25) + i*s(5)),
                (cx + s(60), head_y + s(15) + i*s(10)),
                s(2)
            )

        # Paws (Front Left - Waving)
        paw_x, paw_y = cx - s(60), cy + s(120)
        # Rotate paw point around pivot
        # Simple representation: just move it based on angle
        wave_offset_x = s(30) * (self.paw_angle / 45.0)
        wave_offset_y = -s(30) * abs(self.paw_angle / 45.0)

        pygame.draw.circle(
            surface, WHITE,
            (int(paw_x + wave_offset_x), int(paw_y + wave_offset_y)),
            s(25)
        )
        
        # Paws (Front Right)
        pygame.draw.circle(surface, WHITE, (cx + s(60), cy + s(120)), s(25))
        
        # Paws (Back)
        pygame.draw.circle(surface, WHITE, (cx - s(80), cy + s(130)), s(25))
        pygame.draw.circle(surface, WHITE, (cx + s(80), cy + s(130)), s(25))

# Initialize Cat
cat = Cat(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100, scale=2.0)


# Actions
def action_jump():
    cat.jump()


def action_meow():
    global show_meow
    show_meow = 60  # frames
    cat.open_mouth()


def action_tongue():
    cat.stick_tongue_out()


def action_change_bg():
    global background_color
    # Use a palette of dark colors to avoid flashing bright lights
    dark_colors = [
        (0, 60, 0),      # Dark Green
        (60, 0, 0),      # Dark Red
        (0, 0, 60),      # Dark Blue
        (60, 0, 60),     # Dark Purple
        (0, 60, 60),     # Dark Teal
        (60, 60, 0),     # Dark Olive
        (80, 20, 50),    # Dark Pink
        (30, 30, 30),    # Dark Grey
        (20, 40, 60),    # Dark Slate
        (40, 20, 0),     # Dark Brown
    ]
    background_color = random.choice(dark_colors)


def action_add_shape():
    shape_type = random.choice(['circle', 'rect'])
    color = (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(20, 100)
    background_shapes.append({
        'type': shape_type,
        'color': color,
        'x': x,
        'y': y,
        'size': size
    })
    if len(background_shapes) > 20:
        background_shapes.pop(0)


def action_clear_shapes():
    global background_shapes
    background_shapes = []


def action_wave():
    cat.wave()


def action_chase_ball():
    global ball_pos
    ball_pos = (
        random.randint(100, SCREEN_WIDTH - 100),
        random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 100)
    )
    cat.target_x = ball_pos[0]


def action_reset_pos():
    cat.target_x = SCREEN_WIDTH // 2

# Map keys to actions
actions = [
    action_jump,
    action_meow,
    action_tongue,
    action_change_bg,
    action_add_shape,
    action_wave,
    action_chase_ball,
    action_reset_pos,
    action_clear_shapes
]

# Generate a mapping for many keys
key_mapping = {}
# Alphanumeric keys
for key_code in range(32, 127):  # ASCII printable
    try:
        key_mapping[key_code] = random.choice(actions)
    except Exception:
        pass

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 72)

running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Check for exit combo: Ctrl + Alt + E + X
            keys = pygame.key.get_pressed()
            if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and \
               (keys[pygame.K_LALT] or keys[pygame.K_RALT]) and \
               keys[pygame.K_e] and keys[pygame.K_x]:
                running = False

            # Execute action mapped to key
            if event.key < 128 and event.key in key_mapping:
                key_mapping[event.key]()
            else:
                # Fallback for special keys or unmapped
                random.choice(actions)()

            # Stop waving if not pressing wave key (simulated)
            if event.key != pygame.K_w:
                cat.stop_wave()

    # Update
    cat.update()
    if show_meow > 0:
        show_meow -= 1

    if ball_pos:
        if abs(cat.x - ball_pos[0]) < 10:
            ball_pos = None  # Caught it

    # Draw
    screen.fill(background_color)

    # Draw background shapes
    for shape in background_shapes:
        if shape['type'] == 'circle':
            pygame.draw.circle(
                screen, shape['color'],
                (shape['x'], shape['y']), shape['size']
            )
        elif shape['type'] == 'rect':
            pygame.draw.rect(
                screen, shape['color'],
                (shape['x'], shape['y'], shape['size'], shape['size'])
            )

    # Draw ball if exists
    if ball_pos:
        pygame.draw.circle(screen, (255, 0, 0), ball_pos, 20)

    # Draw Cat
    cat.draw(screen)

    # Draw Meow Bubble
    if show_meow > 0:
        bubble_x, bubble_y = int(cat.x) + 100, int(cat.y) - 200
        pygame.draw.ellipse(screen, WHITE, (bubble_x, bubble_y, 200, 100))
        pygame.draw.polygon(screen, WHITE, [
            (bubble_x + 20, bubble_y + 80),
            (bubble_x + 50, bubble_y + 80),
            (int(cat.x) + 50, int(cat.y) - 100)
        ])
        text = font.render("MIAU!", True, BLACK)
        screen.blit(text, (bubble_x + 30, bubble_y + 25))

    # Instructions (small)
    small_font = pygame.font.SysFont(None, 24)
    exit_text = small_font.render("Exit: Ctrl + Alt + E + X", True, WHITE)
    screen.blit(exit_text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
