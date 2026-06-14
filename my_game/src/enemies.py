import os
# pyrefly: ignore [missing-import]
import pygame
from src.config import (
    TILE_SIZE,
    ENEMY_SPEED,
    IMAGES_DIR,
    NEON_PURPLE,
    NEON_PINK,
    BLACK
)

class MushroomEnemy(pygame.sprite.Sprite):
    """
    MushroomEnemy patrols back and forth within a range.
    Uses exception handling for asset loading and falls back to a custom shape.
    """
    def __init__(self, x, y, patrol_dist=128):
        super().__init__()
        self.min_x = x - patrol_dist
        self.max_x = x + patrol_dist
        
        self.image = self._load_sprite()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.speed = ENEMY_SPEED
        self.direction = 1 # 1 = right, -1 = left
        self.carrying = None # Holds a carried collectible item
        self.x = float(x)

    def _load_sprite(self):
        """
        Attempts to load the enemy sprite.
        Catches exceptions and creates a custom procedural one-eyed mushroom.
        """
        image_path = os.path.join(IMAGES_DIR, 'enemy.png')
        size = int(TILE_SIZE * 1.5)
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Enemy image not found at {image_path}")
            
            sprite = pygame.image.load(image_path).convert_alpha()
            sprite = pygame.transform.scale(sprite, (size, size))
            return sprite
            
        except Exception as e:
            print(f"[Warning] Failed to load enemy sprite: {e}. Generating procedural fallback.")
            
            # Procedural fallback: One-eyed purple/pink mushroom enemy
            fallback_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Stem (beige color)
            pygame.draw.rect(fallback_surf, (230, 210, 180), (16, 24, 16, 24), border_radius=4)
            
            # Cap (Neon Purple/Pink dome)
            pygame.draw.ellipse(fallback_surf, NEON_PURPLE, (2, 6, size - 4, 24))
            
            # Eye core (Greenish white eye as seen in the image)
            pygame.draw.circle(fallback_surf, (150, 255, 150), (size // 2, 18), 7)
            pygame.draw.circle(fallback_surf, BLACK, (size // 2, 18), 3)
            
            # Spikes/Horns (tiny pink triangles or circles on top)
            pygame.draw.circle(fallback_surf, NEON_PINK, (8, 8), 4)
            pygame.draw.circle(fallback_surf, NEON_PINK, (size - 8, 8), 4)
            
            return fallback_surf

    def update(self, platforms, player_center=None, collectibles=None):
        """Moves the enemy, targeting nearby collectibles or player, otherwise patrolling."""
        chasing = False
        speed = self.speed
        
        # If carrying an item, update its position relative to the zombie's head
        if self.carrying is not None:
            self.carrying.rect.centerx = self.rect.centerx
            self.carrying.rect.bottom = self.rect.top - 2
            
        # Target nearby collectibles to carry
        if self.carrying is None and collectibles is not None:
            closest_item = None
            closest_dist = float('inf')
            
            for item in collectibles:
                dx = item.rect.centerx - self.rect.centerx
                dy = item.rect.centery - self.rect.centery
                if abs(dx) < 250 and abs(dy) < 100:
                    dist = dx * dx + dy * dy
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_item = item
                        
            if closest_item is not None:
                dx = closest_item.rect.centerx - self.rect.centerx
                if abs(dx) > 4:
                    self.direction = 1 if dx > 0 else -1
                else:
                    self.direction = 0 # Prevent oscillation next to gold/diamond
                chasing = True
                
                # Pick up if colliding
                if self.rect.colliderect(closest_item.rect):
                    self.carrying = closest_item
                    try:
                        # Remove from the ground collectibles group
                        collectibles.remove(closest_item)
                    except Exception:
                        pass
                    self.carrying.rect.centerx = self.rect.centerx
                    self.carrying.rect.bottom = self.rect.top - 2
                    chasing = False
                    
        # Chase the player if not seeking gold/diamond
        if not chasing and self.carrying is None and player_center is not None:
            px, py = player_center
            dx = px - self.rect.centerx
            dy = py - self.rect.centery
            # Aggro range: 300px horizontal, 100px vertical
            if abs(dx) < 300 and abs(dy) < 100:
                chasing = True
                if abs(dx) > 6:
                    self.direction = 1 if dx > 0 else -1
                    speed = self.speed * 1.4 # Speed up when chasing player
                else:
                    self.direction = 0 # Prevent oscillation next to player
                
        # Perform horizontal movement
        self.x += speed * self.direction
        self.rect.x = int(self.x)
        
        # Check patrol boundaries (only when not chasing/seeking/carrying)
        if not chasing and self.carrying is None:
            if self.direction == 0:
                self.direction = 1 # Resume patrol default direction if idle
                
            if self.rect.x <= self.min_x:
                self.rect.x = self.min_x
                self.x = float(self.rect.x)
                self.direction = 1
            elif self.rect.x >= self.max_x:
                self.rect.x = self.max_x
                self.x = float(self.rect.x)
                self.direction = -1
            
        # Check wall collisions
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.direction > 0: # Hit right wall
                    self.rect.right = platform.rect.left
                    self.x = float(self.rect.x)
                    self.direction = -1
                elif self.direction < 0: # Hit left wall
                    self.rect.left = platform.rect.right
                    self.x = float(self.rect.x)
                    self.direction = 1

    def draw(self, surface):
        """Draws the enemy, optionally flipped depending on patrol direction, and any carried item."""
        if self.direction < 0:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
            
        # Draw the carried item above the enemy's head
        if self.carrying is not None:
            surface.blit(self.carrying.image, self.carrying.rect)
