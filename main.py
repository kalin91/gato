import pygame
import random
import sys
import os

# Initialize Pygame
pygame.init()

# Screen setup
# Try to detect multiple monitors and span across them
try:
    sizes = pygame.display.get_desktop_sizes()
    # Assume horizontal layout: sum widths, max height
    SCREEN_WIDTH = sum(w for w, h in sizes)
    SCREEN_HEIGHT = max(h for w, h in sizes)
    # Position window at top-left of the first monitor
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
except (AttributeError, pygame.error):
    # Fallback for older pygame or errors
    info = pygame.display.Info()
    SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

pygame.display.set_caption("Gato Interactivo")

# Load Sounds
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    
    sound_meow = pygame.mixer.Sound(os.path.join(assets_dir, "Meow.ogg"))
    sound_tongue = pygame.mixer.Sound(os.path.join(assets_dir, "BounceYoFrankie.flac"))
    sound_jump = pygame.mixer.Sound(os.path.join(assets_dir, "qubodup-cfork-ccby3-jump.ogg"))
except Exception as e:
    print(f"Warning: Could not load sounds: {e}")
    sound_meow = None
    sound_tongue = None
    sound_jump = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
PINK = (255, 192, 203)

# Global state
background_color = (30, 30, 30)
background_shapes = []
particles = []
fishes = []
show_meow = 0
ball_pos = None


class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.original_lifetime = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            radius = int(5 * (self.lifetime / self.original_lifetime))
            if radius > 0:
                pygame.draw.circle(
                    surface, self.color, (int(self.x), int(self.y)), radius
                )


class Fish:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = 0
        self.vx = random.uniform(-2, 2)
        self.on_ground = False
        self.color = (100, 150, 200)

    def update(self):
        if not self.on_ground:
            self.vy += 0.5  # Gravity
            self.y += self.vy
            self.x += self.vx

            if self.y > SCREEN_HEIGHT - 20:
                self.y = SCREEN_HEIGHT - 20
                self.vy = -self.vy * 0.5  # Bounce
                if abs(self.vy) < 1:
                    self.on_ground = True
                    self.vy = 0
                    self.vx = 0

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        # Body
        pygame.draw.ellipse(surface, self.color, (cx - 15, cy - 10, 30, 20))
        # Tail
        pygame.draw.polygon(surface, self.color, [
            (cx - 15, cy),
            (cx - 25, cy - 10),
            (cx - 25, cy + 10)
        ])
        # Eye
        pygame.draw.circle(surface, WHITE, (cx + 5, cy - 3), 3)
        pygame.draw.circle(surface, BLACK, (cx + 6, cy - 3), 1)


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
        self.is_crouching = False

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

        # Clamp position to keep cat just within "fully offscreen" limits
        # Body width is roughly s(100) to left and right, but tail extends further
        # s(100) with scale 2.0 is 200. Tail is s(120) + jitter.
        # We use s(200) to be safe and ensure it's completely hidden.
        limit_padding = int(200 * self.scale)
        min_x = -limit_padding
        max_x = SCREEN_WIDTH + limit_padding

        if self.x < min_x:
            self.x = min_x
            # Also clamp target so we can return immediately
            if self.target_x < min_x:
                self.target_x = min_x
        elif self.x > max_x:
            self.x = max_x
            # Also clamp target so we can return immediately
            if self.target_x > max_x:
                self.target_x = max_x

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = -20
            if sound_jump:
                sound_jump.play()

    def open_mouth(self):
        self.mouth_state = 'open'
        self.mouth_timer = 60

    def stick_tongue_out(self):
        self.mouth_state = 'tongue'
        self.mouth_timer = 60

    def crouch(self):
        self.is_crouching = True

    def stand(self):
        self.is_crouching = False

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

        # Adjust dimensions for crouching
        if self.is_crouching:
            body_rect = (cx - s(110), cy + s(40), s(220), s(110))
            head_cy = cy + s(10)
        else:
            body_rect = (cx - s(100), cy, s(200), s(150))
            head_cy = cy - s(60)

        # Tail
        # slight jitter
        tail_end_x = cx + s(120) + s(30) * random.choice([-1, 1]) * 0.1
        tail_end_y = cy - s(50) + s(20) * random.choice([-1, 1]) * 0.1
        pygame.draw.line(
            surface, GRAY, (cx + s(80), cy + s(50)),
            (tail_end_x, tail_end_y), s(15)
        )

        # Body
        pygame.draw.ellipse(surface, GRAY, body_rect)

        # Head (Moved down to connect with body)
        head_y = head_cy
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
    if sound_meow:
        sound_meow.play()


def action_tongue():
    cat.stick_tongue_out()
    if sound_tongue:
        sound_tongue.play()


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
# Define reserved keys to exclude from random mapping
reserved_keys = [
    pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
    pygame.K_SPACE,
    ord('a'), ord('d'), ord('w'), ord('s'),
    ord('A'), ord('D'), ord('W'), ord('S')
]

# Alphanumeric keys
for key_code in range(32, 127):  # ASCII printable
    if key_code in reserved_keys:
        continue
    try:
        key_mapping[key_code] = random.choice(actions)
    except Exception:
        pass

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 72)

running = True
while running:
    # Mouse position for fairy dust
    mx, my = pygame.mouse.get_pos()
    # Add dust (Light Blue / Cyan)
    particles.append(Particle(
        mx, my, (173, 216, 230),
        (random.uniform(-1, 1), random.uniform(-1, 1)), 30
    ))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click - Fish
                fishes.append(Fish(event.pos[0], event.pos[1]))
            elif event.button == 3:  # Right click - Explosion
                for _ in range(20):
                    color = random.choice([
                        (255, 0, 255), (0, 255, 255), (255, 255, 0)
                    ])
                    vel = (random.uniform(-5, 5), random.uniform(-5, 5))
                    particles.append(Particle(
                        event.pos[0], event.pos[1], color, vel, 60
                    ))
        elif event.type == pygame.KEYDOWN:
            # Check for exit combo: Ctrl + Alt + E + X
            keys = pygame.key.get_pressed()
            if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and \
               (keys[pygame.K_LALT] or keys[pygame.K_RALT]) and \
               keys[pygame.K_e] and keys[pygame.K_x]:
                running = False

            # Jump action (Space, Up, W)
            if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
                cat.jump()

            # Execute action mapped to key
            if event.key < 128 and event.key in key_mapping:
                key_mapping[event.key]()
            elif event.key not in reserved_keys and event.key < 128:
                # Fallback for special keys or unmapped
                random.choice(actions)()

            # Stop waving if not pressing wave key (simulated)
            if event.key != pygame.K_w:
                cat.stop_wave()

    # Continuous key checks for movement and crouching
    keys = pygame.key.get_pressed()
    
    # Left (Left Arrow, A)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        cat.target_x -= 10
    
    # Right (Right Arrow, D)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        cat.target_x += 10

    # Crouch (Down Arrow, S)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        cat.crouch()
    else:
        cat.stand()

    # Update
    cat.update()
    if show_meow > 0:
        show_meow -= 1

    # Update particles
    for p in particles[:]:
        p.update()
        if p.lifetime <= 0:
            particles.remove(p)

    # Update fishes
    for f in fishes[:]:
        f.update()

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

    # Draw particles
    for p in particles:
        p.draw(screen)

    # Draw fishes
    for f in fishes:
        f.draw(screen)

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
