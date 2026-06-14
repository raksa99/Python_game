import os
import sys
import random
import math
# pyrefly: ignore [missing-import]
import pygame
# pyrefly: ignore [missing-import]
from PIL import Image, ImageDraw, ImageFont

# Adjust path to find src packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TILE_SIZE,
    NEON_BLUE,
    NEON_PURPLE,
    NEON_PINK,
    WHITE,
    GOLD,
    IMAGES_DIR,
    MUSIC_DIR,
    SFX_DIR
)
from src.player import Player
from src.enemies import MushroomEnemy
from src.levels import Level


class Particle:
    """Represents a visual effect particle emitted during game actions (jumping, hit, stomp)."""
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime

    def update(self, dt=1):
        """Moves particle, applies friction, gravity, and decreases remaining lifetime."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.vy += 0.1  # Gravity effect
        self.vx *= 0.98  # Air friction resistance

    def draw(self, surface):
        """Draws the particle, shrinking its size dynamically as it gets closer to death."""
        if self.lifetime <= 0:
            return
        ratio = self.lifetime / self.max_lifetime
        current_size = max(1, int(self.size * ratio))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), current_size)


class Game:
    """
    Main Game Controller.
    Initializes Pygame, loads assets, handles game states (START, PLAYING, GAME_OVER, VICTORY),
    runs the game update loop, processes inputs/collisions, and renders the HUD.
    """
    def __init__(self):
        # Initialize Pygame and audio mixer
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except Exception as e:
            print(f"[Warning] Audio mixer failed to initialize: {e}. Running without sound.")
            self.audio_enabled = False

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ដំណើរផ្សងព្រេងរកកំណប់")
        self.clock = pygame.time.Clock()
        
        # Game states: "START", "PLAYING", "GAME_OVER", "VICTORY"
        self.state = "START"
        self.current_level_num = 1
        self.max_levels = 10
        self.score = 0
        
        # Level Timer settings
        self.level_time_limit = 120  # 2 minutes per level (120 seconds)
        self.level_timer = self.level_time_limit
        self.timer_accumulator = 0
        
        # Load system fonts safely with fallbacks
        try:
            self.title_font = pygame.font.SysFont("khmer sangam mn", 32, bold=True)
            self.hud_font = pygame.font.SysFont("khmer sangam mn", 18, bold=True)
            self.ui_font = pygame.font.SysFont("khmer sangam mn", 14, bold=True)
        except Exception:
            self.title_font = pygame.font.SysFont("courier", 32, bold=True)
            self.hud_font = pygame.font.SysFont("courier", 18, bold=True)
            self.ui_font = pygame.font.SysFont("courier", 14, bold=True)

        # Background image & stars
        self.background_img = self._load_background()
        self.background_stars = [
            (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT // 2 + 100), random.randint(0, 100))
            for _ in range(40)
        ]

        # Audio Assets loading
        self.sounds = {}
        if self.audio_enabled:
            self._load_audio()
            
        self.particles = []
        self.reset_game()

    def render_khmer(self, text, size, color=(255, 255, 255)):
        """
        Renders Khmer Unicode text using Pillow (PIL) for correct glyph shaping/combining.
        Pygame's default renderer cannot stack Khmer sub-consonants/vowels properly, 
        so we render the text to an RGBA Pillow image and convert it to a Pygame Surface.
        """
        if isinstance(color, pygame.Color):
            color_tuple = (color.r, color.g, color.b)
        else:
            color_tuple = color
            
        cache_key = (text, size, color_tuple)
        if not hasattr(self, '_khmer_cache'):
            self._khmer_cache = {}
            
        if cache_key in self._khmer_cache:
            return self._khmer_cache[cache_key]
            
        # Try loading different Khmer system fonts
        font_choices = [
            "Khmer Sangam MN",
            "/System/Library/Fonts/Supplemental/Khmer Sangam MN.ttc",
            "Khmer MN",
            "Arial Khmer"
        ]
        pil_font = None
        for font_name in font_choices:
            try:
                pil_font = ImageFont.truetype(font_name, size)
                break
            except Exception:
                continue
        if pil_font is None:
            pil_font = ImageFont.load_default()

        try:
            bbox = pil_font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            pad = 4
            img = Image.new("RGBA", (max(1, w + pad * 2), max(1, h + pad * 2)), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((pad - bbox[0], pad - bbox[1]), text, font=pil_font, fill=color_tuple + (255,))
            raw_data = img.tobytes("raw", "RGBA")
            pygame_surf = pygame.image.fromstring(raw_data, img.size, "RGBA")
        except Exception as e:
            fallback_font = pygame.font.SysFont("courier", size, bold=True)
            pygame_surf = fallback_font.render(text, True, color)
            
        self._khmer_cache[cache_key] = pygame_surf
        return pygame_surf

    def _load_background(self):
        """Loads the background.png city skyline image from assets."""
        bg_path = os.path.join(IMAGES_DIR, 'background.png')
        try:
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path).convert()
                return pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            pass
        return None

    def _load_audio(self):
        """Loads background music and sound effect WAV assets."""
        # Load background music loop
        bg_music_paths = [
            os.path.join(MUSIC_DIR, 'bg_music.mp3'),
            os.path.join(MUSIC_DIR, 'bg_music.wav')
        ]
        for path in bg_music_paths:
            try:
                if os.path.exists(path):
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1)  # Infinite loop
                    break
            except Exception as e:
                print(f"[Warning] Failed to play background music: {e}")
                
        # Load Sound Effects (SFX)
        sfx_files = {
            'jump': 'jump.wav',
            'collect': 'laser.wav',
            'damage': 'damage.wav',
            'win': 'level_up.wav',
            'game_over': 'game_over.wav',
            'victory': 'victory.wav'
        }
        for key, filename in sfx_files.items():
            path = os.path.join(SFX_DIR, filename)
            try:
                if os.path.exists(path):
                    self.sounds[key] = pygame.mixer.Sound(path)
                    self.sounds[key].set_volume(0.5)
            except Exception as e:
                print(f"[Warning] Failed to load SFX '{key}': {e}")

    def play_sfx(self, sound_name):
        """Safely plays sound effect from cache."""
        if self.audio_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass

    def reset_game(self):
        """Resets score, active level, and respawns game objects."""
        self.score = 0
        self.current_level_num = 1
        self.player = None
        self.load_level(self.current_level_num)

    def load_level(self, level_num):
        """Loads level layout, resets stage timers, and spawns level elements."""
        self.current_level_num = level_num
        self.level_timer = self.level_time_limit
        self.timer_accumulator = 0
        self.particles = []
        
        # Load Level config
        self.level = Level(self.current_level_num)
        
        # Spawn Player (Adjust Y so bottom aligns with the platform top)
        px, py = self.level.player_spawn
        player_h = int(TILE_SIZE * 1.7)
        py = py - (player_h - TILE_SIZE)
        
        if not hasattr(self, 'player') or self.player is None:
            self.player = Player(px, py)
        else:
            self.player.spawn_pos = (px, py)
            self.player.reset_to_spawn()
            
        self.player.score = self.score  # Carry score over between levels

        # Spawn Patrolling Enemies
        self.enemies = pygame.sprite.Group()
        enemy_h = int(TILE_SIZE * 1.5)
        for ex, ey in self.level.enemies_data:
            ey = ey - (enemy_h - TILE_SIZE)
            enemy = MushroomEnemy(ex, ey)
            self.enemies.add(enemy)

    def spawn_particles(self, x, y, color, count=10):
        """Spawns visual particle bursts."""
        for _ in range(count):
            vx = random.uniform(-2.5, 2.5)
            vy = random.uniform(-3.5, 1.0)
            size = random.randint(2, 4)
            lifetime = random.randint(12, 24)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def handle_events(self):
        """Processes event queue, state transitions, and restart commands."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if self.state == "START" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.state = "PLAYING"
                elif self.state == "PLAYING" and event.key == pygame.K_ESCAPE:
                    self.state = "START"
                elif self.state in ("GAME_OVER", "VICTORY") and event.key == pygame.K_r:
                    self.reset_game()
                    self.state = "PLAYING"

    def update(self):
        """Updates physics, timers, particle cycles, and triggers collision checks."""
        if self.state != "PLAYING":
            return

        dt = self.clock.get_time()
        
        # 1. Update Level Timer
        self.timer_accumulator += dt
        if self.timer_accumulator >= 1000:  # 1 second elapsed
            self.level_timer -= 1
            self.timer_accumulator -= 1000
            
            # Out-of-time penalty
            if self.level_timer <= 0:
                self.player.take_damage()
                self.play_sfx('damage')
                self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, NEON_PINK, 15)
                self.level_timer = self.level_time_limit
                
        # 2. Check Game Over state
        if self.player.lives <= 0:
            self.play_sfx('game_over')
            self.state = "GAME_OVER"
            return

        # 3. Process Player input triggers (Jump particles and sound triggers)
        jumped, attacked = self.player.get_input()
        if jumped:
            self.play_sfx('jump')
            self.spawn_particles(self.player.rect.centerx, self.player.rect.bottom, NEON_BLUE, 10)
        if attacked:
            self.play_sfx('collect')
            swing_x = self.player.rect.right if self.player.facing_right else self.player.rect.left
            self.spawn_particles(swing_x, self.player.rect.centery, GOLD, 8)

        # 4. Update Game objects (Scale updates by Delta-Time factor)
        time_factor = dt / 16.67
        self.player.update(self.level.platforms, time_factor)
        self.enemies.update(self.level.platforms, self.player.rect.center, self.level.collectibles)
        self.level.collectibles.update()

        # 5. Update Particles
        for p in self.particles[:]:
            p.update(time_factor)
            if p.lifetime <= 0:
                self.particles.remove(p)

        # 6. Screen fall detection
        if self.player.rect.top > SCREEN_HEIGHT:
            self.play_sfx('damage')
            self.spawn_particles(self.player.rect.centerx, SCREEN_HEIGHT - 20, NEON_PINK, 15)
            self.player.take_damage()
            self.player.reset_to_spawn()

        # 7. Resolve game collisions
        self.check_collisions()

    def check_collisions(self):
        """Resolves intersections between player, enemies, collectibles, and goal portal."""
        # 1. Player Scepter Attack vs. Enemies
        if self.player.is_attacking:
            # Create a front swing hitbox extending 75px
            if self.player.facing_right:
                attack_rect = pygame.Rect(self.player.rect.right, self.player.rect.top, 75, self.player.rect.height)
            else:
                attack_rect = pygame.Rect(self.player.rect.left - 75, self.player.rect.top, 75, self.player.rect.height)
            
            for enemy in list(self.enemies):
                if attack_rect.colliderect(enemy.rect):
                    self.play_sfx('collect')
                    self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, (100, 255, 100), 20)
                    if enemy.carrying is not None:
                        # Drop carried item back to the ground
                        enemy.carrying.rect.center = enemy.rect.center
                        enemy.carrying.base_y = enemy.rect.centery
                        self.level.collectibles.add(enemy.carrying)
                        enemy.carrying = None
                    enemy.kill()
                    self.player.score += 200
                    self.score = self.player.score

        # 2. Player vs. Collectibles
        collected = pygame.sprite.spritecollide(self.player, self.level.collectibles, True)
        for item in collected:
            self.play_sfx('collect')
            sparkle_color = GOLD if item.kind == "gold" else NEON_BLUE
            self.spawn_particles(item.rect.centerx, item.rect.centery, sparkle_color, 12)
            self.player.score += 200 if item.kind == "diamond" else 100
            self.score = self.player.score

        # 3. Player vs. Enemies (Stomp vs. Damage contact)
        enemy_hit = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if enemy_hit:
            enemy = enemy_hit[0]
            # If landing on the enemy's head, squash them (stomp behavior)
            if self.player.velocity.y > 0 and self.player.rect.bottom <= enemy.rect.top + 12:
                self.play_sfx('collect')
                self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, (100, 255, 100), 20)
                if enemy.carrying is not None:
                    enemy.carrying.rect.center = enemy.rect.center
                    enemy.carrying.base_y = enemy.rect.centery
                    self.level.collectibles.add(enemy.carrying)
                    enemy.carrying = None
                enemy.kill()
                self.player.velocity.y = -8  # Bounce player upwards
                self.player.score += 200
                self.score = self.player.score
            else:
                # Lateral contact causes player to take damage
                damaged = self.player.take_damage()
                if damaged:
                    self.play_sfx('damage')
                    self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, NEON_PINK, 15)
                    
        # 4. Player vs. Goal Portal (Level transition)
        if self.level.goal_sprite and self.player.rect.colliderect(self.level.goal_sprite.rect):
            if self.current_level_num < self.max_levels:
                self.play_sfx('win')
                self.load_level(self.current_level_num + 1)
            else:
                self.play_sfx('victory')
                self.state = "VICTORY"

    def draw_background(self):
        """Draws background skyline graphic or a fallback linear gradient with stars."""
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))
            return
            
        # Draw fallback linear gradient (purple -> deep space blue)
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(15 * (1 - ratio) + 5 * ratio)
            g = int(8 * (1 - ratio) + 2 * ratio)
            b = int(32 * (1 - ratio) + 12 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Draw twinkling stars
        ticks = pygame.time.get_ticks()
        for star in self.background_stars:
            twinkle = (ticks // 250 + star[2]) % 3
            size = 1 + twinkle
            pygame.draw.circle(self.screen, (200, 240, 255), (star[0], star[1]), size)

    def draw_heart(self, x, y, size=14):
        """Draws a procedural heart shape for lives display in HUD."""
        color = NEON_PINK
        pygame.draw.circle(self.screen, color, (x - size // 4, y - size // 4), size // 4)
        pygame.draw.circle(self.screen, color, (x + size // 4, y - size // 4), size // 4)
        points = [(x - size // 2, y - size // 8), (x + size // 2, y - size // 8), (x, y + size // 2)]
        pygame.draw.polygon(self.screen, color, points)

    def draw_hud(self):
        """Renders HUD showing lives, level, score, title, and remaining time in Khmer."""
        # Top banner panel
        pygame.draw.rect(self.screen, (20, 15, 35, 120), (0, 0, SCREEN_WIDTH, 50))
        
        # Lives
        lives_label = self.render_khmer("ជីវិត: ", 18, WHITE)
        self.screen.blit(lives_label, (20, 15))
        for i in range(self.player.lives):
            self.draw_heart(80 + i * 22, 26)

        # Level Info
        level_label = self.render_khmer(f"វគ្គ {self.current_level_num}", 18, NEON_BLUE)
        self.screen.blit(level_label, (20, 42))

        # Game Title
        title_label = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 18, WHITE)
        title_rect = title_label.get_rect(center=(SCREEN_WIDTH // 2, 25))
        self.screen.blit(title_label, title_rect)

        # Score
        score_label = self.render_khmer(f"ពិន្ទុ: {self.player.score:05d}", 18, WHITE)
        self.screen.blit(score_label, (SCREEN_WIDTH - 200, 15))

        # Time remaining (MM:SS)
        minutes = self.level_timer // 60
        seconds = self.level_timer % 60
        time_label = self.render_khmer(f"ពេលវេលា: {minutes:02d}:{seconds:02d}", 18, WHITE)
        self.screen.blit(time_label, (SCREEN_WIDTH - 200, 42))

    def draw_controls_box(self):
        """Draws HUD controls guide overlay panel (Only on Level 1)."""
        box_rect = pygame.Rect(40, 120, 240, 165)
        
        # Semi-transparent overlay box
        overlay = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (10, 5, 25, 180), (0, 0, box_rect.width, box_rect.height), border_radius=10)
        pygame.draw.rect(overlay, NEON_BLUE, (0, 0, box_rect.width, box_rect.height), width=2, border_radius=10)
        self.screen.blit(overlay, box_rect.topleft)
        
        title_surf = self.render_khmer("ការបញ្ជា", 18, NEON_BLUE)
        self.screen.blit(title_surf, (box_rect.x + 20, box_rect.y + 15))
        
        up_text = self.render_khmer("W / UP / SPACE -> លោត", 14, WHITE)
        left_text = self.render_khmer("A / LEFT     -> ឆ្វេង", 14, WHITE)
        right_text = self.render_khmer("D / RIGHT    -> ស្តាំ", 14, WHITE)
        attack_text = self.render_khmer("F / J        -> វាយ", 14, GOLD)
        
        self.screen.blit(up_text, (box_rect.x + 15, box_rect.y + 55))
        self.screen.blit(left_text, (box_rect.x + 15, box_rect.y + 80))
        self.screen.blit(right_text, (box_rect.x + 15, box_rect.y + 105))
        self.screen.blit(attack_text, (box_rect.x + 15, box_rect.y + 130))

    def draw_start_screen(self):
        """Renders title menu screen."""
        self.draw_background()
        
        title_surf = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 32, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        
        # Shadow glow offsets
        for offset in range(3, 0, -1):
            glow = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 32, NEON_PURPLE)
            self.screen.blit(glow, (title_rect.x + offset, title_rect.y + offset))
            
        self.screen.blit(title_surf, title_rect)
        
        # Blinking start prompt
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            prompt = self.render_khmer("ចុច ENTER ដើម្បីលេង", 18, NEON_PINK)
            prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(prompt, prompt_rect)

        # Controls tutorial box
        box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 80, 240, 165)
        overlay = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (15, 10, 30, 220), (0, 0, box_rect.width, box_rect.height), border_radius=8)
        pygame.draw.rect(overlay, NEON_PURPLE, (0, 0, box_rect.width, box_rect.height), width=2, border_radius=8)
        self.screen.blit(overlay, box_rect.topleft)
        
        c_title = self.render_khmer("ការណែនាំពីការបញ្ជា", 18, NEON_BLUE)
        up_t = self.render_khmer("W / UP / SPACE: លោត", 14, WHITE)
        l_t = self.render_khmer("A / LEFT: ទៅឆ្វេង", 14, WHITE)
        r_t = self.render_khmer("D / RIGHT: ទៅស្តាំ", 14, WHITE)
        attack_t = self.render_khmer("F / J: វាយប្រហារ", 14, GOLD)
        
        self.screen.blit(c_title, (box_rect.x + 18, box_rect.y + 15))
        self.screen.blit(up_t, (box_rect.x + 15, box_rect.y + 55))
        self.screen.blit(l_t, (box_rect.x + 15, box_rect.y + 80))
        self.screen.blit(r_t, (box_rect.x + 15, box_rect.y + 105))
        self.screen.blit(attack_t, (box_rect.x + 15, box_rect.y + 130))

    def draw_game_over_screen(self):
        """Renders failure restart menu screen."""
        self.draw_background()
        
        title_surf = self.render_khmer("ចប់ហ្គេម", 32, NEON_PINK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(title_surf, title_rect)
        
        score_surf = self.render_khmer(f"ពិន្ទុចុងក្រោយ: {self.score}", 18, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 25))
        self.screen.blit(score_surf, score_rect)
        
        prompt_surf = self.render_khmer("ចុច 'R' ដើម្បីលេងម្តងទៀត", 18, NEON_BLUE)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 75))
        self.screen.blit(prompt_surf, prompt_rect)

    def draw_victory_screen(self):
        """Renders victory end screen."""
        self.draw_background()
        
        title_surf = self.render_khmer("ជោគជ័យ!", 32, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        
        glow = self.render_khmer("ជោគជ័យ!", 32, WHITE)
        self.screen.blit(glow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)
        
        sub = self.render_khmer("អ្នកបានឈ្នះ ដំណើរផ្សងព្រេងរកកំណប់!", 18, NEON_BLUE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(sub, sub_rect)
        
        score_surf = self.render_khmer(f"ពិន្ទុសរុប: {self.score}", 18, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(score_surf, score_rect)
        
        prompt_surf = self.render_khmer("ចុច 'R' ដើម្បីលេងម្តងទៀត", 18, NEON_PINK)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(prompt_surf, prompt_rect)

    def draw(self):
        """Draws scene depending on active state."""
        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PLAYING":
            self.draw_background()
            
            # Draw level objects
            self.level.platforms.draw(self.screen)
            self.level.collectibles.draw(self.screen)
            
            if self.level.goal_sprite:
                self.screen.blit(self.level.goal_sprite.image, self.level.goal_sprite.rect)
                
            for enemy in self.enemies:
                enemy.draw(self.screen)
                
            self.player.draw(self.screen)
            
            # Draw golden attack swing arc
            if self.player.is_attacking:
                if self.player.facing_right:
                    pygame.draw.arc(self.screen, GOLD, (self.player.rect.right - 10, self.player.rect.top - 10, 90, self.player.rect.height + 20), -math.pi/3, math.pi/3, 4)
                else:
                    pygame.draw.arc(self.screen, GOLD, (self.player.rect.left - 80, self.player.rect.top - 10, 90, self.player.rect.height + 20), 2*math.pi/3, 4*math.pi/3, 4)

            # Draw particles
            for p in self.particles:
                p.draw(self.screen)
            
            # HUD metrics overlay
            self.draw_hud()
            
            # Tutorial controls box (Level 1 only)
            if self.current_level_num == 1:
                self.draw_controls_box()
                
        elif self.state == "GAME_OVER":
            self.draw_game_over_screen()
        elif self.state == "VICTORY":
            self.draw_victory_screen()

        pygame.display.flip()

    def run(self):
        """Starts core update-and-draw game loop at locked FPS."""
        try:
            while True:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(FPS)
        except Exception as e:
            print(f"[Critical Error] Game crashed: {e}")
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
