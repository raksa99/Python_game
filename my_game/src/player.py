import os
# pyrefly: ignore [missing-import]
import pygame
from src.config import (
    TILE_SIZE,
    GRAVITY,
    TERMINAL_VELOCITY,
    PLAYER_SPEED,
    PLAYER_JUMP_SPEED,
    PLAYER_LIVES,
    IMAGES_DIR,
    NEON_BLUE,
    WHITE
)

class Player(pygame.sprite.Sprite):
    """
    Player class representing the main astronaut character.
    Handles user keyboard inputs, applying gravity, collision resolution, and animation cycles.
    """
    def __init__(self, x, y):
        super().__init__()
        self.spawn_pos = (x, y)
        
        # Load animation frames for all states (idle, walking, attacking)
        self.idle_right, self.idle_left = self._load_idle_sprites()
        self.walk_right, self.walk_left = self._load_walk_sprites()
        self.attack_right, self.attack_left = self._load_attack_sprites()
        
        self.image = self.idle_right
        self.rect = self.image.get_rect(topleft=self.spawn_pos)
        
        # Animation state
        self.anim_index = 0.0
        self.anim_speed = 0.15  # Rate at which walk frames cycle (scaled by dt)
        
        # Physics state
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        
        # Gameplay stats
        self.lives = PLAYER_LIVES
        self.score = 0
        self.invulnerable = False
        self.invulnerable_timer = 0
        
        # Attack state
        self.is_attacking = False
        self.attack_duration = 0
        self.attack_cooldown = 0
        
    def _load_single_frame(self, filename, width, height, fallback_color, draw_extra=None):
        """Helper function to load a single frame, scaling it and providing a simple fallback if missing."""
        path = os.path.join(IMAGES_DIR, filename)
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (width, height))
            else:
                raise FileNotFoundError()
        except Exception:
            # Fallback procedurally generated astronaut capsule shape
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(surf, fallback_color, (4, 4, width - 8, height - 8), border_radius=8)
            pygame.draw.rect(surf, (200, 240, 255), (10, 10, width - 20, 14), border_radius=4)
            pygame.draw.rect(surf, WHITE, (4, 4, width - 8, height - 8), width=2, border_radius=8)
            if draw_extra:
                draw_extra(surf, width, height)
            return surf

    def _load_idle_sprites(self):
        """Loads player_idle.png and creates left-facing version."""
        w = int(TILE_SIZE * 1.3)
        h = int(TILE_SIZE * 1.7)
        right = self._load_single_frame('player_idle.png', w, h, NEON_BLUE)
        left = pygame.transform.flip(right, True, False)
        return right, left

    def _load_walk_sprites(self):
        """Loads walking animation frames."""
        w = int(TILE_SIZE * 1.3)
        h = int(TILE_SIZE * 1.7)
        right_frames = []
        left_frames = []
        for i in range(4):
            # Walk fallback scrolls up/down to simulate steps
            def draw_walk_fallback(surf, width, height, index=i):
                if index % 2 == 0:
                    surf.scroll(0, 2)
            right = self._load_single_frame(f'player_walk_{i}.png', w, h, NEON_BLUE, draw_walk_fallback)
            left = pygame.transform.flip(right, True, False)
            right_frames.append(right)
            left_frames.append(left)
        return right_frames, left_frames

    def _load_attack_sprites(self):
        """Loads player_attack.png and creates left-facing version."""
        w = int(TILE_SIZE * 1.3)
        h = int(TILE_SIZE * 1.7)
        def draw_scepter(surf, width, height):
            pygame.draw.line(surf, (255, 215, 0), (width - 10, height // 2), (width, height // 2), width=3)
        right = self._load_single_frame('player_attack.png', w, h, NEON_BLUE, draw_scepter)
        left = pygame.transform.flip(right, True, False)
        return right, left

    def get_input(self):
        """Processes keyboard input for player movement, jump, and attack actions."""
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        
        # 1. Walk inputs
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity.x = -PLAYER_SPEED
            self.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity.x = PLAYER_SPEED
            self.facing_right = True
            
        # 2. Jump input (Allowed only if on the ground)
        jumped = False
        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.velocity.y = PLAYER_JUMP_SPEED
            self.on_ground = False
            jumped = True
            
        # 3. Attack input (Triggers scepter swing hitbox with cooldown)
        attacked = False
        if (keys[pygame.K_f] or keys[pygame.K_j]) and self.attack_cooldown <= 0:
            self.is_attacking = True
            self.attack_duration = 15
            self.attack_cooldown = 30
            attacked = True
            
        return jumped, attacked

    def apply_gravity(self):
        """Applies downward gravitational force to vertical velocity, capped at terminal velocity."""
        self.velocity.y += GRAVITY
        if self.velocity.y > TERMINAL_VELOCITY:
            self.velocity.y = TERMINAL_VELOCITY

    def update(self, platforms, dt=1):
        """Updates physics position, resolves collisions, and updates timer states."""
        # Horizontal Movement and Collision Resolution
        self.rect.x += self.velocity.x
        self.check_horizontal_collisions(platforms)
        
        # Vertical Movement and Collision Resolution
        self.apply_gravity()
        self.rect.y += self.velocity.y
        self.check_vertical_collisions(platforms)
        
        # Invulnerability blinking timer
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        # Scepter attack timers
        if self.is_attacking:
            self.attack_duration -= dt
            if self.attack_duration <= 0:
                self.is_attacking = False
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
                
        # Update animations
        self.animate(dt)

    def animate(self, dt):
        """Cycles through animation frames depending on current player action/movement state."""
        if self.is_attacking:
            self.image = self.attack_right if self.facing_right else self.attack_left
            self.anim_index = 0.0
        elif not self.on_ground:
            # Use walking frame 1 as the jumping/airborne frame
            self.image = self.walk_right[1] if self.facing_right else self.walk_left[1]
            self.anim_index = 0.0
        elif self.velocity.x != 0:
            # Walk cycle animation
            self.anim_index += self.anim_speed * dt
            if self.anim_index >= len(self.walk_right):
                self.anim_index = 0.0
            idx = int(self.anim_index)
            self.image = self.walk_right[idx] if self.facing_right else self.walk_left[idx]
        else:
            # Idle animation
            self.anim_index = 0.0
            self.image = self.idle_right if self.facing_right else self.idle_left

    def check_horizontal_collisions(self, platforms):
        """Resolves horizontal overlaps, pushing player back out of platform boundaries."""
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:  # Moving right -> Hit left wall
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:  # Moving left -> Hit right wall
                    self.rect.left = platform.rect.right

    def check_vertical_collisions(self, platforms):
        """Resolves vertical overlaps. Sets on_ground status and resets vertical velocity."""
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:  # Falling -> Landed on floor
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:  # Jumping -> Bunted ceiling
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = 0

    def take_damage(self):
        """Applies damage, deducting life and activating temporal invulnerability."""
        if not self.invulnerable:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_timer = 120  # ~2 seconds duration
            return True
        return False

    def reset_to_spawn(self):
        """Resets astronaut position to spawn point and clears velocities (e.g. on fall)."""
        self.rect.topleft = self.spawn_pos
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False

    def draw(self, surface):
        """Draws player sprite to the display surface. Handles invulnerability blinking."""
        if self.invulnerable and (pygame.time.get_ticks() // 100) % 2 == 0:
            return  # Skip draw frame to create flashing feedback
            
        surface.blit(self.image, self.rect)
