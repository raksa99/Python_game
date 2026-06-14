import os
import math
# pyrefly: ignore [missing-import]
import pygame
from src.config import (
    TILE_SIZE,
    NEON_PURPLE,
    NEON_BLUE,
    GOLD,
    WHITE,
    IMAGES_DIR
)

class Platform(pygame.sprite.Sprite):
    """A solid tile that the player and enemies can walk on."""
    _cached_image = None

    def __init__(self, x, y):
        super().__init__()
        if Platform._cached_image is None:
            image_path = os.path.join(IMAGES_DIR, 'stone_ancient.png')
            try:
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Platform image not found at {image_path}")
                img = pygame.image.load(image_path).convert_alpha()
                Platform._cached_image = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            except Exception as e:
                print(f"[Warning] Failed to load platform image: {e}. Falling back to neon procedural tile.")
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                surf.fill(NEON_PURPLE)
                pygame.draw.rect(surf, NEON_BLUE, (0, 0, TILE_SIZE, 4))
                pygame.draw.rect(surf, (10, 5, 20), (0, TILE_SIZE - 4, TILE_SIZE, 4))
                Platform._cached_image = surf
        self.image = Platform._cached_image
        self.rect = self.image.get_rect(topleft=(x, y))



class Collectible(pygame.sprite.Sprite):
    """Collectible items such as gold coins or diamonds."""
    def __init__(self, x, y, kind="gold"):
        super().__init__()
        self.kind = kind
        self.image = self._create_image()
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
        
        # Bobbing floating animation parameters
        self.base_y = self.rect.y
        self.bob_speed = 0.1
        self.bob_height = 4
        self.bob_angle = 0

    def _create_image(self):
        filenames = ["gold.png"] if self.kind == "gold" else ["daimond.png", "diamond.png"]
        image_path = None
        for filename in filenames:
            path = os.path.join(IMAGES_DIR, filename)
            if os.path.exists(path):
                image_path = path
                break
                
        size = 32
        try:
            if not image_path or not os.path.exists(image_path):
                raise FileNotFoundError(f"Collectible image not found for kind: {self.kind}")
            sprite = pygame.image.load(image_path).convert_alpha()
            return pygame.transform.scale(sprite, (size, size))
        except Exception as e:
            # Clean procedural fallbacks (scaled to 30x30)
            surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            if self.kind == "gold":
                # Gold coin
                pygame.draw.circle(surf, GOLD, (15, 15), 12)
                pygame.draw.circle(surf, (200, 150, 0), (15, 15), 12, width=2)
                pygame.draw.circle(surf, (255, 235, 100), (15, 15), 6) # highlight
            else: # "diamond"
                # Cyan diamond shape
                points = [(15, 3), (27, 15), (15, 27), (3, 15)]
                pygame.draw.polygon(surf, (0, 220, 255), points)
                pygame.draw.polygon(surf, WHITE, points, width=2)
            return surf

    def update(self):
        """Bobs the collectible item slightly up and down for a visual glow/float effect."""
        self.bob_angle += self.bob_speed
        self.rect.y = self.base_y + int(math.sin(self.bob_angle) * self.bob_height)


class Goal(pygame.sprite.Sprite):
    """The finish line gate/portal of each level."""
    _cached_image = None

    def __init__(self, x, y):
        super().__init__()
        if Goal._cached_image is None:
            image_path = os.path.join(IMAGES_DIR, 'temple_door.png')
            try:
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Goal image not found at {image_path}")
                img = pygame.image.load(image_path).convert_alpha()
                w, h = int(TILE_SIZE * 1.8), int(TILE_SIZE * 2.5)
                Goal._cached_image = pygame.transform.scale(img, (w, h))
            except Exception as e:
                print(f"[Warning] Failed to load goal image: {e}. Falling back to neon doorway.")
                w, h = int(TILE_SIZE * 1.8), int(TILE_SIZE * 2.5)
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(surf, (0, 0, 0, 150), (4, 0, w - 8, h), border_radius=6)
                pygame.draw.rect(surf, NEON_BLUE, (4, 0, w - 8, h), width=3, border_radius=6)
                pygame.draw.circle(surf, GOLD, (w // 2, h // 2), 4)
                Goal._cached_image = surf
                
        self.image = Goal._cached_image
        self.rect = self.image.get_rect(topleft=(x, y))



# ASCII levels grid size: 32 columns wide, 18 rows high.
# Legend:
# ' ' = Air/Empty
# 'X' = Solid Platform
# 'P' = Player spawn position
# 'E' = Enemy spawn position
# 'F' = Fruit (orange)
# 'S' = Star
# 'G' = Goal Portal (Requires 2 tiles high, placed at bottom tile)

LEVELS_DATA = {
    1: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "            S     S             ",
        "           XXX   XXX            ",
        "                                ",
        "                                ",
        "      F   E           F         ",
        "     XXX XXX         XXX        ",
        "                                ",
        "  P         E                G  ",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    2: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "             S S                ",
        "            XXXXX               ",
        "                                ",
        "       F             F          ",
        "      XXX           XXX         ",
        "                                ",
        "    E     E       E     E       ",
        "   XXXXXXXXXXXXXXXXXXXXXXX      ",
        "                                ",
        " P                           G  ",
        "XXXX   XXXX   XXXX   XXXX   XXXX",
        "XXXX   XXXX   XXXX   XXXX   XXXX"
    ],
    3: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "           S     S              ",
        "          XXX   XXX             ",
        "                                ",
        "       F             F          ",
        "      XXX           XXX         ",
        "                                ",
        "    P                           ",
        "  XXXXXX                      G ",
        "          X     X     X     XXXX",
        "          X  E  X  E  X  E  XXXX",
        "         XXXXXXXXXXXXXXXXXXXXXXX",
        "         XXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    4: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "  S       F       F          S  ",
        " XXX     XXX     XXX        XXX ",
        "                                ",
        "    P                           ",
        "   XXX                          ",
        "                                ",
        "        E                       ",
        "     XXXXXXX                    ",
        "                                ",
        "                 E      E     G ",
        "             XXXXXXXXXXXXXXXXXXX",
        "             XXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    5: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "  F             S             F ",
        " XXX           XXX           XXX",
        "                                ",
        "                                ",
        "      E                 E       ",
        "    XXXXX             XXXXX     ",
        "                                ",
        "                                ",
        "  P       E         E        G  ",
        "XXXXXX   XXXXXX   XXXXXX   XXXXX",
        "XXXXXX   XXXXXX   XXXXXX   XXXXX",
        "XXXXXX   XXXXXX   XXXXXX   XXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    6: [
        "                                ",
        "                                ",
        "                                ",
        "            S S S               ",
        "            XXXXX               ",
        "                                ",
        "          E       E             ",
        "        XXXXX   XXXXX           ",
        "                                ",
        "      F               F         ",
        "     XXX             XXX        ",
        "                                ",
        "   P                         G  ",
        "  XXX                       XXX ",
        "                                ",
        "       E   E         E   E      ",
        "XXXXXXXXXXXXXXXX   XXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXX   XXXXXXXXXXXXX"
    ],
    7: [
        "                                ",
        "                                ",
        "                                ",
        "                             G  ",
        "                            XXX ",
        "                         F      ",
        "                        XXX     ",
        "                     S          ",
        "                    XXX         ",
        "                 F              ",
        "                XXX             ",
        "             E                  ",
        "            XXX                 ",
        "         F                      ",
        "        XXX                     ",
        "  P                             ",
        "XXXXXXXX                        ",
        "XXXXXXXX                        "
    ],
    8: [
        "                                ",
        "                                ",
        "                                ",
        "                                ",
        "      S                 S       ",
        "     XXX               XXX      ",
        "                                ",
        "  F                         F   ",
        " XXX                       XXX  ",
        "                                ",
        "    E  E  E         E  E  E     ",
        "   XXXXXXXXX       XXXXXXXXX    ",
        "                                ",
        " P                           G  ",
        "XXX                         XXX ",
        "                                ",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    9: [
        "                                ",
        "                                ",
        "                                ",
        "                             G  ",
        "                            XXX ",
        "                         F      ",
        "                       XXXX     ",
        "                     S          ",
        "                   XXXX         ",
        "                 F              ",
        "               XXXX             ",
        "             E                  ",
        "           XXXX                 ",
        "         F                      ",
        "       XXXX                     ",
        "  P                               ",
        "XXXXXX                          ",
        "XXXXXX                          "
    ],
    10: [
        "                                ",
        "             S   S              ",
        "            XXXXXXX             ",
        "                                ",
        "        F             F         ",
        "       XXX           XXX        ",
        "                                ",
        "    E     E         E     E     ",
        "   XXXXXXXXX       XXXXXXXXX    ",
        "                                ",
        "  F                         F   ",
        " XXX                       XXX  ",
        "                                ",
        "    P      E   E   E         G  ",
        "  XXXXX   XXXXXXXXXXX      XXXX ",
        "                                ",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ]
}


class Level:
    """
    Constructs a platformer level based on the ASCII map for level_num.
    Parses elements into pygame sprite groups and tracks spawn points.
    """
    def __init__(self, level_num):
        self.level_num = level_num
        self.platforms = pygame.sprite.Group()
        self.enemies_data = [] # Stores coordinate tuples and patrol distances
        self.collectibles = pygame.sprite.Group()
        self.player_spawn = (100, 300) # Default
        self.goal_sprite = None
        
        self.load_data()

    def load_data(self):
        """Parses the layout grid for this level number."""
        try:
            grid = LEVELS_DATA.get(self.level_num, LEVELS_DATA[1]) # Fallback to level 1
            
            for row_idx, row in enumerate(grid):
                for col_idx, char in enumerate(row):
                    x = col_idx * TILE_SIZE
                    y = row_idx * TILE_SIZE
                    
                    if char == 'X':
                        platform = Platform(x, y)
                        self.platforms.add(platform)
                    elif char == 'P':
                        self.player_spawn = (x, y)
                    elif char == 'E':
                        # Add enemy spawn coordinates and patrol width
                        self.enemies_data.append((x, y))
                    elif char == 'F':
                        gold_item = Collectible(x, y, "gold")
                        self.collectibles.add(gold_item)
                    elif char == 'S':
                        diamond_item = Collectible(x, y, "diamond")
                        self.collectibles.add(diamond_item)
                    elif char == 'G':
                        # Goal portal is 2.5 tiles high, place it correctly (topleft starts at y)
                        goal_w = int(TILE_SIZE * 1.8)
                        goal_h = int(TILE_SIZE * 2.5)
                        self.goal_sprite = Goal(x - (goal_w - TILE_SIZE) // 2, y - (goal_h - TILE_SIZE))
        except Exception as e:
            print(f"[Critical Error] Failed to load level {self.level_num} layout: {e}. Reverting to default platform.")
            # Safety fallback: create a basic flat platform so player has ground
            self.player_spawn = (100, 300)
            self.platforms.add(Platform(100, 400))
