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
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.vy += 0.1
        self.vx *= 0.98

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        ratio = self.lifetime / self.max_lifetime
        current_size = max(1, int(self.size * ratio))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), current_size)



class Game:
    """
    Main Game Controller.
    Manages initialization, game loop, input handling, rendering, 
    level advancement, collision processing, HUD, and exception handling.
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
        pygame.display.set_caption("Angkor Jump - Em Raksa")
        self.clock = pygame.time.Clock()
        
        # Game states: "START", "PLAYING", "GAME_OVER", "VICTORY"
        self.state = "START"
        self.current_level_num = 1
        self.max_levels = 10
        self.score = 0
        
        # Level Timer settings
        self.level_time_limit = 120 # 2 minutes per level (120 seconds)
        self.level_timer = self.level_time_limit
        self.timer_accumulator = 0
        
        # Load system fonts safely with try-except fallback
        try:
            self.title_font = pygame.font.SysFont("khmer sangam mn", 32, bold=True)
            self.hud_font = pygame.font.SysFont("khmer sangam mn", 18, bold=True)
            self.ui_font = pygame.font.SysFont("khmer sangam mn", 14, bold=True)
        except Exception:
            try:
                self.title_font = pygame.font.SysFont("khmer mn", 32, bold=True)
                self.hud_font = pygame.font.SysFont("khmer mn", 18, bold=True)
                self.ui_font = pygame.font.SysFont("khmer mn", 14, bold=True)
            except Exception:
                try:
                    self.title_font = pygame.font.SysFont("kokonor", 32, bold=True)
                    self.hud_font = pygame.font.SysFont("kokonor", 18, bold=True)
                    self.ui_font = pygame.font.SysFont("kokonor", 14, bold=True)
                except Exception:
                    print("[Warning] Khmer system fonts not found. Falling back to Courier.")
                    self.title_font = pygame.font.SysFont("courier", 32, bold=True)
                    self.hud_font = pygame.font.SysFont("courier", 18, bold=True)
                    self.ui_font = pygame.font.SysFont("courier", 14, bold=True)

        # Background image & stars for fallback rendering
        self.background_img = self._load_background()
        self.background_stars = [
            (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT // 2 + 100), random.randint(0, 100))
            for _ in range(40)
        ]

        # Audio Assets
        self.sounds = {}
        if self.audio_enabled:
            self._generate_default_sfx()
            self._load_audio()
            
        self.particles = []
        # Initialize game objects
        self.reset_game()

    def render_khmer(self, text, size, color=(255, 255, 255)):
        """Renders Khmer Unicode text using Pillow for correct text shaping and returns a Pygame Surface."""
        if isinstance(color, pygame.Color):
            color_tuple = (color.r, color.g, color.b)
        else:
            color_tuple = color
            
        cache_key = (text, size, color_tuple)
        if not hasattr(self, '_khmer_cache'):
            self._khmer_cache = {}
            
        if cache_key in self._khmer_cache:
            return self._khmer_cache[cache_key]
            
        try:
            pil_font = ImageFont.truetype("Khmer Sangam MN", size)
            # print(f"[Info] Loaded Khmer Sangam MN successfully for size {size}")
        except Exception:
            try:
                pil_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Khmer Sangam MN.ttc", size)
                # print(f"[Info] Loaded Khmer Sangam MN from Supplemental path successfully for size {size}")
            except Exception:
                try:
                    pil_font = ImageFont.truetype("Khmer MN", size)
                    # print(f"[Info] Loaded Khmer MN successfully for size {size}")
                except Exception:
                    try:
                        pil_font = ImageFont.truetype("Arial Khmer", size)
                        # print(f"[Info] Loaded Arial Khmer successfully for size {size}")
                    except Exception as e:
                        pil_font = ImageFont.load_default()
                        print(f"[Warning] Failed to load any Khmer font: {e}. Loaded default font.")

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
            print(f"[Warning] Pillow render failed: {e}. Falling back to pygame SysFont.")
            fallback_font = pygame.font.SysFont("courier", size, bold=True)
            pygame_surf = fallback_font.render(text, True, color)
            
        self._khmer_cache[cache_key] = pygame_surf
        return pygame_surf

    def _load_background(self):
        """Attempts to load the background city image."""
        bg_path = os.path.join(IMAGES_DIR, 'background.png')
        try:
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Background not found at {bg_path}")
            bg = pygame.image.load(bg_path).convert()
            return pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print(f"[Warning] Failed to load background: {e}. Drawing neon procedural gradient.")
            return None

    def _generate_default_sfx(self):
        """Generates simple retro synthesizer sound effects and music loop if files are missing."""
        import wave
        import struct
        import math
        
        # 1. Generate SFX files
        try:
            os.makedirs(SFX_DIR, exist_ok=True)
            
            sfx_configs = {
                'jump.wav': (600, 0.15, 'jump'),
                'laser.wav': (800, 0.2, 'collect'),
                'damage.wav': (180, 0.3, 'damage'),
                'level_up.wav': (400, 0.4, 'win'),
                'game_over.wav': (250, 0.6, 'damage'),
                'victory.wav': (520, 0.8, 'win')
            }
            
            for filename, (freq, dur, sfx_type) in sfx_configs.items():
                path = os.path.join(SFX_DIR, filename)
                if not os.path.exists(path):
                    print(f"[Info] Generating retro SFX file: {filename}")
                    sample_rate = 44100
                    num_samples = int(dur * sample_rate)
                    with wave.open(path, 'w') as wav_file:
                        wav_file.setparams((1, 2, sample_rate, num_samples, 'NONE', 'not compressed'))
                        for i in range(num_samples):
                            t = float(i) / sample_rate
                            if sfx_type == 'jump':
                                current_freq = freq + (i / num_samples) * 500
                            elif sfx_type == 'collect':
                                current_freq = freq - (i / num_samples) * 400
                            elif sfx_type == 'damage':
                                current_freq = freq - (i / num_samples) * 120
                            elif sfx_type == 'win':
                                segment = num_samples // 4
                                if i < segment:
                                    current_freq = freq
                                elif i < 2 * segment:
                                    current_freq = freq + 150
                                elif i < 3 * segment:
                                    current_freq = freq + 300
                                else:
                                    current_freq = freq + 450
                            else:
                                current_freq = freq
                                
                            current_freq = max(50.0, current_freq)
                            value = math.sin(2.0 * math.pi * current_freq * t)
                            fade_out = 1.0 - (float(i) / num_samples)
                            amplitude = int(value * 32767.0 * 0.4 * fade_out)
                            data = struct.pack('<h', amplitude)
                            wav_file.writeframesraw(data)
        except Exception as e:
            print(f"[Warning] Failed to generate SFX files: {e}")

        # 2. Generate Background Music loop if missing
        try:
            os.makedirs(MUSIC_DIR, exist_ok=True)
            music_path = os.path.join(MUSIC_DIR, 'bg_music.wav')
            if not os.path.exists(music_path) and not os.path.exists(os.path.join(MUSIC_DIR, 'bg_music.mp3')):
                print("[Info] Generating retro background music loop...")
                sample_rate = 22050
                duration = 8.0
                num_samples = int(duration * sample_rate)
                melody = [110, 110, 130.8, 130.8, 146.8, 146.8, 164.8, 164.8,
                          146.8, 146.8, 130.8, 130.8, 110, 110, 164.8, 196.0]
                step_duration = 0.5
                samples_per_step = int(step_duration * sample_rate)
                
                with wave.open(music_path, 'w') as wav_file:
                    wav_file.setparams((1, 2, sample_rate, num_samples, 'NONE', 'not compressed'))
                    for i in range(num_samples):
                        t = float(i) / sample_rate
                        step_idx = (i // samples_per_step) % len(melody)
                        note_freq = melody[step_idx]
                        
                        step_sample_idx = i % samples_per_step
                        decay = 1.0 - (float(step_sample_idx) / samples_per_step) * 0.8
                        
                        value = math.sin(2.0 * math.pi * note_freq * t)
                        value += 0.25 * math.sin(2.0 * math.pi * (note_freq * 2.0) * t)
                        value = max(-1.0, min(1.0, value))
                        
                        amplitude = int(value * 32767.0 * 0.15 * decay)
                        data = struct.pack('<h', amplitude)
                        wav_file.writeframesraw(data)
        except Exception as e:
            print(f"[Warning] Failed to generate background music: {e}")

    def _load_audio(self):
        """Loads music and sound effects with full exception safety."""
        # Attempt to load BG music
        bg_music_paths = [
            os.path.join(MUSIC_DIR, 'bg_music.mp3'),
            os.path.join(MUSIC_DIR, 'bg_music.wav')
        ]
        
        music_loaded = False
        for path in bg_music_paths:
            try:
                if os.path.exists(path):
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1) # Loop forever
                    music_loaded = True
                    break
            except Exception as e:
                print(f"[Warning] Failed to load/play background music from {path}: {e}")
                
        if not music_loaded:
            print("[Info] Background music not playing.")

        # Attempt to load SFX
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
        """Plays sound effect if audio is enabled and sound is loaded."""
        if self.audio_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"[Warning] Error playing SFX '{sound_name}': {e}")

    def reset_game(self):
        """Full game state reset (score, lives, timer, and active level)."""
        self.score = 0
        self.current_level_num = 1
        self.player = None
        self.load_level(self.current_level_num)

    def load_level(self, level_num):
        """Loads a specific level layout and spawns sprites with Y offsets for scaling."""
        self.current_level_num = level_num
        self.level_timer = self.level_time_limit
        self.timer_accumulator = 0
        self.particles = []
        
        # Load Level layout
        self.level = Level(self.current_level_num)
        
        # Spawn player (offset Y so bottom aligns with the grid block bottom)
        px, py = self.level.player_spawn
        player_h = int(TILE_SIZE * 1.7)
        py = py - (player_h - TILE_SIZE)
        
        if not hasattr(self, 'player') or self.player is None:
            self.player = Player(px, py)
        else:
            self.player.spawn_pos = (px, py)
            self.player.reset_to_spawn()
            
        # Sync total score from previous level
        self.player.score = self.score

        # Spawn enemies (offset Y so bottom aligns with the grid block bottom)
        self.enemies = pygame.sprite.Group()
        enemy_h = int(TILE_SIZE * 1.5)
        for ex, ey in self.level.enemies_data:
            ey = ey - (enemy_h - TILE_SIZE)
            enemy = MushroomEnemy(ex, ey)
            self.enemies.add(enemy)

    def spawn_particles(self, x, y, color, count=10):
        """Spawns neon particle bursts for visual effects."""
        for _ in range(count):
            vx = random.uniform(-2.5, 2.5)
            vy = random.uniform(-3.5, 1.0)
            size = random.randint(2, 4)
            lifetime = random.randint(12, 24)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime))

    def handle_events(self):
        """Processes event queue for game states and player jump triggers."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if self.state == "START":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.state = "PLAYING"
                elif self.state == "PLAYING":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "START"
                elif self.state in ("GAME_OVER", "VICTORY"):
                    if event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "PLAYING"

    def update(self):
        """Updates game state, handles physics, timer, and collision checks."""
        if self.state != "PLAYING":
            return

        dt = self.clock.get_time()
        
        # Tick Timer
        self.timer_accumulator += dt
        if self.timer_accumulator >= 1000: # 1 second elapsed
            self.level_timer -= 1
            self.timer_accumulator -= 1000
            
            # Out of time penalty
            if self.level_timer <= 0:
                self.player.take_damage()
                self.play_sfx('damage')
                self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, NEON_PINK, 15)
                self.level_timer = self.level_time_limit
                
        # Check game over state
        if self.player.lives <= 0:
            self.play_sfx('game_over')
            self.state = "GAME_OVER"
            return

        # Player inputs, jump and attack triggers
        jumped, attacked = self.player.get_input()
        if jumped:
            self.play_sfx('jump')
            self.spawn_particles(self.player.rect.centerx, self.player.rect.bottom, NEON_BLUE, 10)
        if attacked:
            self.play_sfx('collect') # Play sound for scepter attack
            swing_x = self.player.rect.right if self.player.facing_right else self.player.rect.left
            self.spawn_particles(swing_x, self.player.rect.centery, GOLD, 8)

        # Update sprite groups
        self.player.update(self.level.platforms, dt / 16.67)
        self.enemies.update(self.level.platforms, self.player.rect.center, self.level.collectibles)
        self.level.collectibles.update()

        # Update particles
        for p in self.particles[:]:
            p.update(dt / 16.67)
            if p.lifetime <= 0:
                self.particles.remove(p)

        # Check if player falls off the screen
        if self.player.rect.top > SCREEN_HEIGHT:
            self.play_sfx('damage')
            self.spawn_particles(self.player.rect.centerx, SCREEN_HEIGHT - 20, NEON_PINK, 15)
            self.player.take_damage()
            self.player.reset_to_spawn()

        # Handle collisions
        self.check_collisions()

    def check_collisions(self):
        """Checks collisions between player, enemies, collectibles, and goal."""
        # Player Scepter Attack
        if self.player.is_attacking:
            if self.player.facing_right:
                attack_rect = pygame.Rect(self.player.rect.right, self.player.rect.top, 75, self.player.rect.height)
            else:
                attack_rect = pygame.Rect(self.player.rect.left - 75, self.player.rect.top, 75, self.player.rect.height)
            
            for enemy in list(self.enemies):
                if attack_rect.colliderect(enemy.rect):
                    self.play_sfx('collect')
                    self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, (100, 255, 100), 20)
                    if enemy.carrying is not None:
                        enemy.carrying.rect.center = enemy.rect.center
                        enemy.carrying.base_y = enemy.rect.centery
                        self.level.collectibles.add(enemy.carrying)
                        enemy.carrying = None
                    enemy.kill()
                    self.player.score += 200
                    self.score = self.player.score

        # Player and Collectibles
        collected = pygame.sprite.spritecollide(self.player, self.level.collectibles, True)
        for item in collected:
            self.play_sfx('collect')
            sparkle_color = GOLD if item.kind == "gold" else NEON_BLUE
            self.spawn_particles(item.rect.centerx, item.rect.centery, sparkle_color, 12)
            points = 200 if item.kind == "diamond" else 100
            self.player.score += points
            self.score = self.player.score

        # Player and Enemies
        enemy_hit = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if enemy_hit:
            # Check if player lands on top of the enemy (stomp behavior)
            enemy = enemy_hit[0]
            if self.player.velocity.y > 0 and self.player.rect.bottom <= enemy.rect.top + 12:
                self.play_sfx('collect') # Play stomp/collect sound
                self.spawn_particles(enemy.rect.centerx, enemy.rect.centery, (100, 255, 100), 20)
                if enemy.carrying is not None:
                    enemy.carrying.rect.center = enemy.rect.center
                    enemy.carrying.base_y = enemy.rect.centery
                    self.level.collectibles.add(enemy.carrying)
                    enemy.carrying = None
                enemy.kill()
                self.player.velocity.y = -8 # Bounce player up
                self.player.score += 200
                self.score = self.player.score
            else:
                # Regular damage
                damaged = self.player.take_damage()
                if damaged:
                    self.play_sfx('damage')
                    self.spawn_particles(self.player.rect.centerx, self.player.rect.centery, NEON_PINK, 15)
                    
        # Player and Goal portal
        if self.level.goal_sprite and self.player.rect.colliderect(self.level.goal_sprite.rect):
            if self.current_level_num < self.max_levels:
                self.play_sfx('win')
                self.load_level(self.current_level_num + 1)
            else:
                self.play_sfx('victory')
                self.state = "VICTORY"

    def draw_background(self):
        """Draws static/dynamic background elements."""
        if self.background_img:
            self.screen.blit(self.background_img, (0, 0))
            return
            
        # Draw retro neon background gradient
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            # Dark neon purple transitioning to dark deep space blue
            r = int(15 * (1 - ratio) + 5 * ratio)
            g = int(8 * (1 - ratio) + 2 * ratio)
            b = int(32 * (1 - ratio) + 12 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Twinkling stars
        ticks = pygame.time.get_ticks()
        for star in self.background_stars:
            twinkle = (ticks // 250 + star[2]) % 3
            size = 1 + twinkle
            pygame.draw.circle(self.screen, (200, 240, 255), (star[0], star[1]), size)

    def draw_heart(self, x, y, size=14):
        """Draws a beautiful procedural heart vector shape for the HUD."""
        color = NEON_PINK
        # Top round lobes
        pygame.draw.circle(self.screen, color, (x - size // 4, y - size // 4), size // 4)
        pygame.draw.circle(self.screen, color, (x + size // 4, y - size // 4), size // 4)
        # Bottom cone
        points = [
            (x - size // 2, y - size // 8),
            (x + size // 2, y - size // 8),
            (x, y + size // 2)
        ]
        pygame.draw.polygon(self.screen, color, points)

    def draw_hud(self):
        """Renders HUD showing lives, current level, score, title, and level timer."""
        # Top Banner bar (translucent dark border)
        pygame.draw.rect(self.screen, (20, 15, 35, 120), (0, 0, SCREEN_WIDTH, 50))
        
        # 1. Lives Display
        lives_label = self.render_khmer("ជីវិត: ", 18, WHITE)
        self.screen.blit(lives_label, (20, 15))
        for i in range(self.player.lives):
            self.draw_heart(80 + i * 22, 26)

        # 2. Level Identifier
        level_label = self.render_khmer(f"វគ្គ {self.current_level_num}", 18, NEON_BLUE)
        self.screen.blit(level_label, (20, 42))

        # 3. Game Title
        title_label = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 18, WHITE)
        title_rect = title_label.get_rect(center=(SCREEN_WIDTH // 2, 25))
        self.screen.blit(title_label, title_rect)

        # 4. Score Display
        score_label = self.render_khmer(f"ពិន្ទុ: {self.player.score:05d}", 18, WHITE)
        self.screen.blit(score_label, (SCREEN_WIDTH - 200, 15))

        # 5. Timer Format (MM:SS)
        minutes = self.level_timer // 60
        seconds = self.level_timer % 60
        time_str = f"ពេលវេលា: {minutes:02d}:{seconds:02d}"
        time_label = self.render_khmer(time_str, 18, WHITE)
        self.screen.blit(time_label, (SCREEN_WIDTH - 200, 42))

    def draw_controls_box(self):
        """Draws the transparent tutorial controls menu on the left side of the screen."""
        box_rect = pygame.Rect(40, 120, 240, 165)
        
        # Transparent background panel
        overlay = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (10, 5, 25, 180), (0, 0, box_rect.width, box_rect.height), border_radius=10)
        pygame.draw.rect(overlay, NEON_BLUE, (0, 0, box_rect.width, box_rect.height), width=2, border_radius=10)
        self.screen.blit(overlay, box_rect.topleft)
        
        # Heading
        title_surf = self.render_khmer("ការបញ្ជា", 18, NEON_BLUE)
        self.screen.blit(title_surf, (box_rect.x + 20, box_rect.y + 15))
        
        # Instruction text details
        up_text = self.render_khmer("W / UP / SPACE -> លោត", 14, WHITE)
        left_text = self.render_khmer("A / LEFT     -> ឆ្វេង", 14, WHITE)
        right_text = self.render_khmer("D / RIGHT    -> ស្តាំ", 14, WHITE)
        attack_text = self.render_khmer("F / J        -> វាយ", 14, GOLD)
        
        self.screen.blit(up_text, (box_rect.x + 15, box_rect.y + 55))
        self.screen.blit(left_text, (box_rect.x + 15, box_rect.y + 80))
        self.screen.blit(right_text, (box_rect.x + 15, box_rect.y + 105))
        self.screen.blit(attack_text, (box_rect.x + 15, box_rect.y + 130))

    def draw_start_screen(self):
        """Draws start menu screen with glowing title and play prompt."""
        self.draw_background()
        
        # Title box
        title_surf = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 32, NEON_BLUE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        
        # Glowing effect
        for offset in range(3, 0, -1):
            glow_surf = self.render_khmer("ដំណើរផ្សងព្រេងរកកំណប់", 32, NEON_PURPLE)
            self.screen.blit(glow_surf, (title_rect.x + offset, title_rect.y + offset))
            
        self.screen.blit(title_surf, title_rect)
        
        # Start prompt blinking
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            prompt_surf = self.render_khmer("ចុច ENTER ដើម្បីលេង", 18, NEON_PINK)
            prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(prompt_surf, prompt_rect)

        # Draw controls on start screen
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
        """Draws failure restart menu screen."""
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
        """Draws final levels completion screen."""
        self.draw_background()
        
        title_surf = self.render_khmer("ជោគជ័យ!", 32, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        
        # Gold glow
        glow_surf = self.render_khmer("ជោគជ័យ!", 32, WHITE)
        self.screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)
        
        sub_surf = self.render_khmer("អ្នកបានឈ្នះ ដំណើរផ្សងព្រេងរកកំណប់!", 18, NEON_BLUE)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(sub_surf, sub_rect)
        
        score_surf = self.render_khmer(f"ពិន្ទុសរុប: {self.score}", 18, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(score_surf, score_rect)
        
        prompt_surf = self.render_khmer("ចុច 'R' ដើម្បីលេងម្តងទៀត", 18, NEON_PINK)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(prompt_surf, prompt_rect)

    def draw(self):
        """Renders scene depending on active state."""
        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PLAYING":
            self.draw_background()
            
            # Draw game sprites
            self.level.platforms.draw(self.screen)
            self.level.collectibles.draw(self.screen)
            
            if self.level.goal_sprite:
                self.screen.blit(self.level.goal_sprite.image, self.level.goal_sprite.rect)
                
            for enemy in self.enemies:
                enemy.draw(self.screen)
                
            self.player.draw(self.screen)
            
            # Draw attack swing arc visual
            if self.player.is_attacking:
                if self.player.facing_right:
                    pygame.draw.arc(self.screen, GOLD, (self.player.rect.right - 10, self.player.rect.top - 10, 90, self.player.rect.height + 20), -math.pi/3, math.pi/3, 4)
                else:
                    pygame.draw.arc(self.screen, GOLD, (self.player.rect.left - 80, self.player.rect.top - 10, 90, self.player.rect.height + 20), 2*math.pi/3, 4*math.pi/3, 4)

            # Draw particles
            for p in self.particles:
                p.draw(self.screen)
            
            # HUD details
            self.draw_hud()
            
            # On Level 1, draw the Controls box on screen as a helper tutorial
            if self.current_level_num == 1:
                self.draw_controls_box()
                
        elif self.state == "GAME_OVER":
            self.draw_game_over_screen()
        elif self.state == "VICTORY":
            self.draw_victory_screen()

        pygame.display.flip()

    def run(self):
        """Starts main loop running at lock FPS."""
        try:
            while True:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(FPS)
        except Exception as e:
            print(f"[Critical Error] Game crash in main loop: {e}")
            pygame.quit()
            sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
