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
    Uses Pygame sprite capabilities and handles input, gravity, and collision.
    """
    def __init__(self, x, y):
        super().__init__()
        self.spawn_pos = (x, y)
        
        # Load animation frames
        self.idle_right, self.idle_left = self._load_idle_sprites()
        self.walk_right, self.walk_left = self._load_walk_sprites()
        self.attack_right, self.attack_left = self._load_attack_sprites()
        
        self.image = self.idle_right
        self.rect = self.image.get_rect(topleft=self.spawn_pos)
        
        # Animation state
        self.anim_index = 0.0
        self.anim_speed = 0.15 # Frames advanced per update step
        
        # Physics state
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        
        # Game stats
        self.lives = PLAYER_LIVES
        self.score = 0
        self.invulnerable = False
        self.invulnerable_timer = 0
        
        # Attack state
        self.is_attacking = False
        self.attack_duration = 0
        self.attack_cooldown = 0
        
    def _load_idle_sprites(self):
        """Loads player_idle.png and creates left-facing version."""
        width = int(TILE_SIZE * 1.3)
        height = int(TILE_SIZE * 1.7)
        
        idle_path = os.path.join(IMAGES_DIR, 'player_idle.png')
        try:
            if os.path.exists(idle_path):
                img = pygame.image.load(idle_path).convert_alpha()
                right = pygame.transform.scale(img, (width, height))
            else:
                raise FileNotFoundError()
        except Exception:
            right = self._create_procedural_sprite(facing_right=True)
            
        left = pygame.transform.flip(right, True, False)
        return right, left

    def _load_walk_sprites(self):
        """Loads walking animation frames."""
        width = int(TILE_SIZE * 1.3)
        height = int(TILE_SIZE * 1.7)
        
        right_frames = []
        left_frames = []
        
        for i in range(4):
            walk_path = os.path.join(IMAGES_DIR, f'player_walk_{i}.png')
            try:
                if os.path.exists(walk_path):
                    img = pygame.image.load(walk_path).convert_alpha()
                    r_img = pygame.transform.scale(img, (width, height))
                    l_img = pygame.transform.flip(r_img, True, False)
                    right_frames.append(r_img)
                    left_frames.append(l_img)
                else:
                    raise FileNotFoundError()
            except Exception:
                surf_r = self._create_procedural_sprite(facing_right=True)
                if i % 2 == 0:
                    surf_r.scroll(0, 2)
                surf_l = pygame.transform.flip(surf_r, True, False)
                right_frames.append(surf_r)
                left_frames.append(surf_l)
                
        return right_frames, left_frames

    def _load_attack_sprites(self):
        """Loads player_attack.png and creates left-facing version."""
        width = int(TILE_SIZE * 1.3)
        height = int(TILE_SIZE * 1.7)
        
        attack_path = os.path.join(IMAGES_DIR, 'player_attack.png')
        try:
            if os.path.exists(attack_path):
                img = pygame.image.load(attack_path).convert_alpha()
                right = pygame.transform.scale(img, (width, height))
            else:
                raise FileNotFoundError()
        except Exception:
            right = self._create_procedural_sprite(facing_right=True)
            pygame.draw.line(right, (255, 215, 0), (width - 10, height // 2), (width, height // 2), width=3)
            
        left = pygame.transform.flip(right, True, False)
        return right, left

    def _create_procedural_sprite(self, facing_right=True):
        """Generates a retro neon astronaut capsule procedurally as fallback."""
        width = int(TILE_SIZE * 1.3)
        height = int(TILE_SIZE * 1.7)
        fallback_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(fallback_surf, NEON_BLUE, (4, 4, width - 8, height - 8), border_radius=8)
        visor_x = 10 if facing_right else 6
        pygame.draw.rect(fallback_surf, (200, 240, 255), (visor_x, 10, width - 16, 16), border_radius=4)
        pygame.draw.rect(fallback_surf, WHITE, (4, 4, width - 8, height - 8), width=2, border_radius=8)
        return fallback_surf

    def get_input(self):
        """Processes keyboard input for player movement, jump, and attack actions."""
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        
        # Move Left
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity.x = -PLAYER_SPEED
            self.facing_right = False
        # Move Right
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity.x = PLAYER_SPEED
            self.facing_right = True
            
        # Jump
        jumped = False
        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.velocity.y = PLAYER_JUMP_SPEED
            self.on_ground = False
            jumped = True
            
        # Attack (F or J)
        attacked = False
        if (keys[pygame.K_f] or keys[pygame.K_j]) and self.attack_cooldown <= 0:
            self.is_attacking = True
            self.attack_duration = 15
            self.attack_cooldown = 30
            attacked = True
            
        return jumped, attacked

    def apply_gravity(self):
        """Applies downward gravitational force to vertical velocity."""
        self.velocity.y += GRAVITY
        if self.velocity.y > TERMINAL_VELOCITY:
            self.velocity.y = TERMINAL_VELOCITY

    def update(self, platforms, dt=1):
        """
        Updates the player state, applying horizontal and vertical movements,
        and checking platform collisions.
        """
        # Horizontal Movement and Collision
        self.rect.x += self.velocity.x
        self.check_horizontal_collisions(platforms)
        
        # Vertical Movement and Collision
        self.apply_gravity()
        self.rect.y += self.velocity.y
        self.check_vertical_collisions(platforms)
        
        # Invulnerability blinking/timer
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                
        # Handle attack timers
        if self.is_attacking:
            self.attack_duration -= dt
            if self.attack_duration <= 0:
                self.is_attacking = False
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
                
        # Handle animation logic
        self.animate(dt)

    def animate(self, dt):
        """Updates player frames based on state and movement."""
        if self.is_attacking:
            if self.facing_right:
                self.image = self.attack_right
            else:
                self.image = self.attack_left
            self.anim_index = 0.0
        elif not self.on_ground:
            # Jump/Air Frame: use walk frame 1
            if self.facing_right:
                self.image = self.walk_right[1]
            else:
                self.image = self.walk_left[1]
            self.anim_index = 0.0
        elif self.velocity.x != 0:
            # Walking frame cycling
            self.anim_index += self.anim_speed * dt
            if self.anim_index >= len(self.walk_right):
                self.anim_index = 0.0
            frame_idx = int(self.anim_index)
            if self.facing_right:
                self.image = self.walk_right[frame_idx]
            else:
                self.image = self.walk_left[frame_idx]
        else:
            # Idle frame
            self.anim_index = 0.0
            if self.facing_right:
                self.image = self.idle_right
            else:
                self.image = self.idle_left

    def check_horizontal_collisions(self, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0: # Moving right
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0: # Moving left
                    self.rect.left = platform.rect.right

    def check_vertical_collisions(self, platforms):
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0: # Falling
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0: # Jumping
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = 0

    def take_damage(self):
        """Applies damage to player if not invulnerable."""
        if not self.invulnerable:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_timer = 120 # 120 frames (~2 sec) invulnerable
            # Do not reset to spawn on enemy collision (only on screen fall)
            return True
        return False

    def reset_to_spawn(self):
        """Resets position to spawn point and cancels velocity."""
        self.rect.topleft = self.spawn_pos
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False

    def draw(self, surface):
        """Draws the player to the surface, handling blink if invulnerable."""
        if self.invulnerable and (pygame.time.get_ticks() // 100) % 2 == 0:
            return # Skip drawing to make blinking effect
            
        surface.blit(self.image, self.rect)
