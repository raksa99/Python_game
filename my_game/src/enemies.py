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

class Zoombie(pygame.sprite.Sprite):
    """
    Zoombie patrolling platform platforms.
    Features:
    1. Chasing nearby collectibles to pick up and carry on its head.
    2. Chasing the player when they step within aggro range.
    3. Patrolling back and forth in a specified bounds.
    """
    def __init__(self, x, y, patrol_dist=128):
        super().__init__()
        self.min_x = x - patrol_dist
        self.max_x = x + patrol_dist
        
        self.image = self._load_sprite()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.speed = ENEMY_SPEED
        self.direction = 1  # 1 = Right, -1 = Left
        self.carrying = None  # Holds collectible object when picked up
        self.x = float(x)

    def _load_sprite(self):
        """Loads the enemy.png sprite from assets, falling back to a simple shape if missing."""
        image_path = os.path.join(IMAGES_DIR, 'enemy.png')
        size = int(TILE_SIZE * 1.5)
        try:
            if os.path.exists(image_path):
                sprite = pygame.image.load(image_path).convert_alpha()
                return pygame.transform.scale(sprite, (size, size))
            else:
                raise FileNotFoundError()
        except Exception:
            # Simple fallback: Neon purple square with eye accents
            fallback = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(fallback, NEON_PURPLE, (4, 4, size - 8, size - 8), border_radius=6)
            pygame.draw.circle(fallback, (150, 255, 150), (size // 2, size // 2), 6)  # Green eye
            pygame.draw.circle(fallback, BLACK, (size // 2, size // 2), 2)  # Pupil
            pygame.draw.circle(fallback, NEON_PINK, (8, 8), 3)  # Left horn
            pygame.draw.circle(fallback, NEON_PINK, (size - 8, 8), 3)  # Right horn
            return fallback

    def update(self, platforms, player_center=None, collectibles=None):
        """Updates AI behavior, coordinates movement, and resolves boundary checks/wall collisions."""
        chasing = False
        current_speed = self.speed
        
        # 1. Update position of carried item relative to zombie's head
        if self.carrying is not None:
            self.carrying.rect.centerx = self.rect.centerx
            self.carrying.rect.bottom = self.rect.top - 2
            
        # 2. Collectibles Interaction AI (Seek nearby coins/diamonds)
        if self.carrying is None and collectibles is not None:
            closest_item = None
            closest_dist = float('inf')
            
            for item in collectibles:
                dx = item.rect.centerx - self.rect.centerx
                dy = item.rect.centery - self.rect.centery
                # Seek only within reasonable range (250px width, 100px height)
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
                    self.direction = 0  # Stop oscillation
                chasing = True
                
                # Pick up if colliding
                if self.rect.colliderect(closest_item.rect):
                    self.carrying = closest_item
                    try:
                        collectibles.remove(closest_item)  # Remove from ground group
                    except Exception:
                        pass
                    chasing = False
                    
        # 3. Player Chasing AI (Aggro range: 300px width, 100px height)
        if not chasing and self.carrying is None and player_center is not None:
            px, py = player_center
            dx = px - self.rect.centerx
            dy = py - self.rect.centery
            if abs(dx) < 300 and abs(dy) < 100:
                chasing = True
                if abs(dx) > 6:
                    self.direction = 1 if dx > 0 else -1
                    current_speed = self.speed * 1.4  # Chases player 40% faster
                else:
                    self.direction = 0  # Stop oscillation
                
        # 4. Movement execution
        self.x += current_speed * self.direction
        self.rect.x = int(self.x)
        
        # 5. Patrol Boundaries (Only when not seeking items or chasing player)
        if not chasing and self.carrying is None:
            if self.direction == 0:
                self.direction = 1  # Resume default patrol direction if idle
                
            if self.rect.x <= self.min_x:
                self.rect.x = self.min_x
                self.x = float(self.rect.x)
                self.direction = 1  # Turn Right
            elif self.rect.x >= self.max_x:
                self.rect.x = self.max_x
                self.x = float(self.rect.x)
                self.direction = -1  # Turn Left
            
        # 6. Wall Collisions (Reverse direction on hitting vertical obstacle)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.direction > 0:  # Moving right -> Turn left
                    self.rect.right = platform.rect.left
                    self.x = float(self.rect.x)
                    self.direction = -1
                elif self.direction < 0:  # Moving left -> Turn right
                    self.rect.left = platform.rect.right
                    self.x = float(self.rect.x)
                    self.direction = 1

    def draw(self, surface):
        """Draws enemy (flipped depending on direction) and their carried item if they have one."""
        if self.direction < 0:
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            surface.blit(self.image, self.rect)
            
        # Draw the carried item floating above the head
        if self.carrying is not None:
            surface.blit(self.carrying.image, self.carrying.rect)
