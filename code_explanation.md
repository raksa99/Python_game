# Game Source Code Explanation Guide

This project is built using Python and Pygame. It is organized into a modular structure where configuration, character logic, levels, and main control flow are separated into individual files.

---

### 1. Game Configuration: [config.py](file:///Users/panha/Desktop/Game%20Jump/my_game/src/config.py)
This file houses all of the static configuration settings, constants, and path directories used across the game so they can be changed easily in one place.

* **Lines 4–7**: Screen and Tile settings (`SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS`, `TILE_SIZE`).
* **Lines 10–11**: Physics constants (`GRAVITY`, `TERMINAL_VELOCITY`).
* **Lines 14–16**: Player settings (`PLAYER_SPEED`, `PLAYER_JUMP_SPEED`, `PLAYER_LIVES`).
* **Line 19**: Zombie/Enemy speed setting (`ENEMY_SPEED`).
* **Lines 23–29**: A curated neon color palette matching the aesthetic of the game.
* **Lines 32–37**: Dynamic absolute directory path generation for loading asset files like images, background music, and sound effects.

---

### 2. Zombie Enemy Behavior: [enemies.py](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py)
This file defines the [Zoombie](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L13) sprite class, controlling its movement, boundary bounds, and interactions with players or objects.

* **Class [Zoombie](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L13)**: Extends `pygame.sprite.Sprite` to manage individual enemies.
  * **`__init__`** ([lines 21–32](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L21-L32)): Sets up the starting position, patrolling boundaries (`min_x`, `max_x`), direction, and carrying state.
  * **`_load_sprite`** ([lines 34–52](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L34-L52)): Loads the sprite image asset from disk or draws a procedural neon square with eyes as a fallback.
  * **`update`** ([lines 54–138](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L54-L138)): Computes the artificial intelligence (AI) logic:
    1. If carrying a collectible, updates the collectible position to hover above the zombie's head.
    2. If empty-handed, checks if a coin or diamond is nearby and chases to pick it up.
    3. If no collectibles are nearby, checks if the player is within range and chases them at 1.4x speed.
    4. Otherwise, default patrolls left/right between its boundary markers.
    5. Reverses direction upon colliding with a wall.
  * **`draw`** ([lines 139–149](file:///Users/panha/Desktop/Game%20Jump/my_game/src/enemies.py#L139-L149)): Draws the zombie (automatically flipping it left or right depending on movement) and the item it is carrying.

---

### 3. Player Control & Physics: [player.py](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py)
This file contains the main [Player](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L16) class representing the playable astronaut character.

* **Class [Player](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L16)**: Extends `pygame.sprite.Sprite` to handle physics, input controls, and health.
  * **`__init__`** ([lines 21–51](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L21-L51)): Initializes variables for position, physics velocity vectors, lives, invulnerability timers, animation states, and scepter swing details.
  * **`_load_single_frame`** ([lines 53–70](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L53-L70)): Loads animation frames from disk, falling back to procedurally drawing a vector astronaut capsule if files are missing.
  * **`_load_idle_sprites`, `_load_walk_sprites`, `_load_attack_sprites`** ([lines 72–105](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L72-L105)): Loads/renders player animation states.
  * **`get_input`** ([lines 107–135](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L107-L135)): Reads keyboard inputs (Arrow keys or WASD to move/jump, Space to jump, and F/J to execute a scepter swing).
  * **`apply_gravity`** ([lines 137–141](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L137-L141)): Pulls the player down, capping it at terminal velocity.
  * **`update`** ([lines 143–170](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L143-L170)): Runs physics coordinates calculations, checks platform collisions, updates invulnerability/cooldown status, and advances animations.
  * **`animate`** ([lines 171–191](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L171-L191)): Cycles walking and idle graphics frames.
  * **`check_horizontal_collisions`** ([lines 192–200](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L192-L200)): Prevents the player from walking through walls.
  * **`check_vertical_collisions`** ([lines 201–213](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L201-L213)): Identifies when the player hits a ceiling (stops upward momentum) or lands on a floor (sets `on_ground = True`).
  * **`take_damage`** ([lines 214–221](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L214-L221)): Deducts a life point and turns on invulnerability mode temporarily.
  * **`reset_to_spawn`** ([lines 223–228](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L223-L228)): Teleports the player back to the start if they fall down.
  * **`draw`** ([lines 229–234](file:///Users/panha/Desktop/Game%20Jump/my_game/src/player.py#L229-L234)): Renders the player, flashing transparently when invulnerable.

---

### 4. Level Parser & Layout: [levels.py](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py)
This file represents level design structures and handles environmental items.

* **Class [Platform](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L14)**: Extends `pygame.sprite.Sprite`. Creates solid terrain building blocks. Utilizes static class caching (`_cached_image`) so the platform graphic is loaded into memory only once rather than for every single block.
* **Class [Collectible](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L40)**: Extends `pygame.sprite.Sprite`.
  * **`update`** ([lines 82–85](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L82-L85)): Uses a sine wave (`math.sin`) to make coins/diamonds float up and down smoothly in mid-air.
* **Class [Goal](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L88)**: Extends `pygame.sprite.Sprite`. Recreates the level finish door portal.
* **Variable [LEVELS_DATA](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L125-L326)**: A map dictionary containing 10 ASCII grids representing level structures (`X` = Platform, `P` = Player, `E` = Zombie, `F` = Gold, `S` = Diamond, `G` = Goal).
* **Class [Level](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L329)**: Responsible for parsing the ASCII string grids into active Pygame sprite groups.
  * **`load_data`** ([lines 341–370](file:///Users/panha/Desktop/Game%20Jump/my_game/src/levels.py#L341-L370)): Iterates through the coordinate matrix, placing platforms, spawning collectibles, saving zombie coordinates, and aligning the door portal.

---

### 5. Main Game Engine: [main.py](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py)
This is the master entry point where the game window is created, the clock runs, and global game state flow is managed.

* **Class [Particle](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L32)**: Represents simple cosmetic physics particles that bounce and fade away when jumping, getting hit, or stomping an enemy.
* **Class [Game](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L61)**:
  * **`__init__`** ([lines 67–116](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L67-L116)): Initializes Pygame modules, display resolution, level state, and audio systems.
  * **`render_khmer`** ([lines 117–167](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L117-L167)): **A specialized rendering function.** Because Pygame's default text renderer struggles with stacking Khmer Unicode sub-consonants/vowels, this function renders the text onto a transparent Pillow (PIL) canvas first, then converts it into a Pygame surface. It caches results for speed.
  * **`_load_audio` & `play_sfx`** ([lines 180–221](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L180-L221)): Loads the sound effects catalog and starts the background track looping.
  * **`load_level`** ([lines 230–259](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L230-L259)): Instantiates the parsed level and populates active sprite lists.
  * **`handle_events`** ([lines 270–285](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L270-L285)): Detects general keys (like hitting Enter to start the game, Escape to exit to the main menu, and R to restart after losing).
  * **`update`** ([lines 286–342](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L286-L342)): Deducts the countdown timer, checks for a Game Over condition, runs object update cycles, and resolves collision outcomes.
  * **`check_collisions`** ([lines 344–408](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L344-408)):
    1. If the player attacks with their scepter, any zombie within the swing box is defeated (and drops any item it was carrying).
    2. Player gathering coins and diamonds to increment the score.
    3. Player vs. Zombie: If the player lands on the zombie's head (stomp), the zombie is squashed and the player bounces. If hit from the side, the player takes damage.
    4. Advancing stages upon reaching the Goal portal.
  * **`draw_hud`** ([lines 439–467](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L439-467)): Draws the overlay showing lives, current level, game title, score, and level timer in Khmer.
  * **`draw`** ([lines 570–612](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L570-612)): Erases the canvas, paints the background layers, platforms, goal, collectibles, active zombies, player, and animations.
  * **`run`** ([lines 614–625](file:///Users/panha/Desktop/Game%20Jump/my_game/main.py#L614-L625)): The game's main loop that processes inputs, updates physics, and draws the screen 60 times per second.
