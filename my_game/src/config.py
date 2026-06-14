import os

# Screen Settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
FPS = 60
TILE_SIZE = 32

# Physics Constants
GRAVITY = 0.6
TERMINAL_VELOCITY = 12

# Player Settings
PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = -15
PLAYER_LIVES = 5

# Enemy Settings
ENEMY_SPEED = 1


# Colors (Harmonious neon palette matching the Angkor Jump image)
BG_DARK = (15, 10, 30)         # Deep purple/black
NEON_BLUE = (0, 220, 255)      # Light blue glow
NEON_PURPLE = (180, 50, 255)   # Purple details
NEON_PINK = (255, 50, 150)     # Neon pink HUD/accents
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)           # Star collectibles

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
MUSIC_DIR = os.path.join(AUDIO_DIR, 'music')
SFX_DIR = os.path.join(AUDIO_DIR, 'sfx')

