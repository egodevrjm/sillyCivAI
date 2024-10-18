import pygame
import sys
import random

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 1024, 768
TILE_SIZE = 64
MAP_WIDTH = 10
MAP_HEIGHT = 10
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
FONT = pygame.font.SysFont(None, 24)

# Colors
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
DARK_GRAY = (50, 50, 50)
GREEN = (34, 139, 34)
BLUE = (70, 130, 180)
BROWN = (139, 69, 19)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)

# Initialize Pygame Window
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Civilization Clone")
clock = pygame.time.Clock()

# Load Sounds
def load_sound(name):
    try:
        sound = pygame.mixer.Sound(f'sounds/{name}')
        return sound
    except pygame.error:
        print(f"Sound file '{name}' not found.")
        return None

move_sound = load_sound('move.mp3')
attack_sound = load_sound('attack.mp3')
build_sound = load_sound('build.mp3')
click_sound = load_sound('click.mp3')
notification_sound = load_sound('notification.mp3')
production_complete_sound = load_sound('production_complete.mp3')
research_complete_sound = load_sound('research_complete.mp3')
hover_sound = load_sound('hover.mp3')

# Load Images Function
def load_image(name, scale=TILE_SIZE):
    try:
        image = pygame.image.load(f'images/{name}').convert_alpha()
        return pygame.transform.scale(image, (scale, scale))
    except pygame.error:
        # If image not found, return a placeholder surface
        placeholder = pygame.Surface((scale, scale))
        placeholder.fill(GRAY)
        pygame.draw.rect(placeholder, BLACK, placeholder.get_rect(), 2)
        text = FONT.render(name.split('.')[0], True, BLACK)
        text_rect = text.get_rect(center=placeholder.get_rect().center)
        placeholder.blit(text, text_rect)
        return placeholder

# Images for units and buildings
IMAGES = {
    'Settler': load_image('settler.png'),
    'Warrior': load_image('warrior.png'),
    'Worker': load_image('worker.png'),
    'City': load_image('city.png'),
    'Farm': load_image('farm.png'),
    'Mine': load_image('mine.png'),
    'Granary': load_image('granary.png'),
    'Monument': load_image('monument.png'),
    'production_settler_icon': load_image('production_settler_icon.png', scale=32),
    'production_worker_icon': load_image('production_worker_icon.png', scale=32),
    'production_warrior_icon': load_image('production_warrior_icon.png', scale=32),
    'production_granary_icon': load_image('production_granary_icon.png', scale=32),
    'production_monument_icon': load_image('production_monument_icon.png', scale=32),
    'research_agriculture_icon': load_image('research_agriculture_icon.png', scale=32),
    'research_mining_icon': load_image('research_mining_icon.png', scale=32),
    'research_bronze_working_icon': load_image('research_bronze_working_icon.png', scale=32),
    'research_masonry_icon': load_image('research_masonry_icon.png', scale=32),
    'research_pottery_icon': load_image('research_pottery_icon.png', scale=32),
    'progress_bar_bg': load_image('progress_bar_bg.png', scale=200),
    'progress_bar_fill': load_image('progress_bar_fill.png', scale=200),
    'close_icon': load_image('close_icon.png', scale=32),  # Add a close icon
}

# Unit Statistics
UNIT_STATS = {
    'Settler': {'Moves': 2, 'Strength': 0, 'Health': 1},
    'Warrior': {'Moves': 2, 'Strength': 2, 'Health': 5},
    'Worker': {'Moves': 2, 'Strength': 0, 'Health': 1},
}

# Production Costs
PRODUCTION_COSTS = {
    'Settler': 10,
    'Worker': 5,
    'Warrior': 5,
    'Granary': 20,
    'Monument': 10,
}

# Buildings List
BUILDINGS = ['Granary', 'Monument']

# Technology Tree
class Technology:
    def __init__(self):
        self.available_techs = {
            'Agriculture': {'cost': 5, 'prerequisites': []},
            'Mining': {'cost': 5, 'prerequisites': []},
            'Bronze Working': {'cost': 10, 'prerequisites': ['Mining']},
            'Masonry': {'cost': 10, 'prerequisites': ['Mining']},
            'Pottery': {'cost': 5, 'prerequisites': ['Agriculture']},
        }
        self.researched_techs = []
        self.current_research = None
        self.progress = 0

    def get_available_techs(self):
        available = []
        for tech, info in self.available_techs.items():
            if tech not in self.researched_techs:
                if all(prereq in self.researched_techs for prereq in info['prerequisites']):
                    available.append(tech)
        return available

    def start_research(self, tech_name):
        if tech_name in self.get_available_techs():
            self.current_research = tech_name
            self.progress = 0
            print(f"Researching {tech_name}")
            if click_sound:
                click_sound.play()
        else:
            print("Invalid technology.")

    def advance_research(self):
        if self.current_research:
            self.progress += 1
            cost = self.available_techs[self.current_research]['cost']
            if self.progress >= cost:
                self.researched_techs.append(self.current_research)
                print(f"Researched {self.current_research}!")
                self.current_research = None
                self.progress = 0
                if research_complete_sound:
                    research_complete_sound.play()
        else:
            pass  # No technology is being researched

# Button Class with Hover Effect and Icons
class Button:
    def __init__(self, text, x, y, width, height, callback, icon=None, color=GRAY, hover_color=DARK_GRAY, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.icon = icon
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.callback = callback
        self.text_color = text_color
        self.font = pygame.font.SysFont(None, 24)

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=5)
        # Draw icon if available
        if self.icon:
            icon_rect = self.icon.get_rect()
            icon_rect.midleft = (self.rect.left + 10, self.rect.centery)
            surface.blit(self.icon, icon_rect)
            # Adjust text position
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(midleft=(self.rect.left + 50, self.rect.centery))
        else:
            # Center text if no icon
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event, pos):
        if self.rect.collidepoint(pos):
            if event.type == pygame.MOUSEMOTION:
                if hover_sound:
                    hover_sound.play()
            self.current_color = self.hover_color
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if click_sound:
                    click_sound.play()
                self.callback()
        else:
            self.current_color = self.color

# Unit Class
class Unit:
    def __init__(self, x, y, owner, unit_type):
        self.x = x
        self.y = y
        self.owner = owner
        self.moves = UNIT_STATS[unit_type]['Moves']
        self.max_moves = UNIT_STATS[unit_type]['Moves']
        self.unit_type = unit_type
        self.health = UNIT_STATS[unit_type]['Health']

    def move_unit(self, dx, dy, game_map):
        new_x = self.x + dx
        new_y = self.y + dy

        # Check bounds and terrain
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            target_tile = game_map.tiles[new_y][new_x]
            if target_tile.terrain_type != 'Water':
                if target_tile.unit and target_tile.unit.owner != self.owner:
                    # Attack
                    self.attack(target_tile.unit)
                elif not target_tile.unit:
                    # Move unit
                    game_map.tiles[self.y][self.x].unit = None
                    self.x = new_x
                    self.y = new_y
                    target_tile.unit = self
                    self.moves -= 1
                    print(f"{self.unit_type} moved to ({self.x}, {self.y})")
                    if move_sound:
                        move_sound.play()
                else:
                    print("Cannot move there.")
            else:
                print("Cannot move into water.")
        else:
            print("Out of bounds.")

    def attack(self, enemy_unit):
        # Simple combat logic
        print(f"{self.unit_type} attacks {enemy_unit.unit_type}!")
        if attack_sound:
            attack_sound.play()
        enemy_unit.health -= UNIT_STATS[self.unit_type]['Strength']
        if enemy_unit.health <= 0:
            print(f"{enemy_unit.unit_type} defeated!")
            enemy_unit.owner.units.remove(enemy_unit)
            self.owner.game_map.tiles[enemy_unit.y][enemy_unit.x].unit = None
            if production_complete_sound:
                production_complete_sound.play()
        self.moves -= 1

    def reset_moves(self):
        self.moves = self.max_moves

    def found_city(self, game_map):
        tile = game_map.tiles[self.y][self.x]
        if tile.city:
            print("A city already exists here.")
            return
        new_city = City(self.x, self.y, self.owner)
        self.owner.cities.append(new_city)
        tile.city = new_city
        # Remove unit after founding a city
        self.owner.units.remove(self)
        tile.unit = None
        print(f"City founded at ({self.x}, {self.y})")
        if build_sound:
            build_sound.play()

    def build_improvement(self, game_map):
        tile = game_map.tiles[self.y][self.x]
        if tile.improvement:
            print("An improvement already exists here.")
            return
        if tile.terrain_type in ['Plains', 'Forest']:
            tile.improvement = 'Farm'
            print("Farm built.")
            if build_sound:
                build_sound.play()
        elif tile.terrain_type == 'Mountain':
            tile.improvement = 'Mine'
            print("Mine built.")
            if build_sound:
                build_sound.play()
        else:
            print("Cannot build an improvement here.")
            return
        self.moves -= 1

# City Class
class City:
    def __init__(self, x, y, owner):
        self.x = x
        self.y = y
        self.owner = owner
        self.name = f"City {len(owner.cities) + 1}"
        self.population = 1
        self.food = 0
        self.food_required = 5
        self.production_queue = []
        self.production_progress = 0

        # Default yields
        self.yields = {'Food': 2, 'Production': 1, 'Gold': 1}

    def produce(self):
        # Accumulate food for population growth
        self.food += self.yields['Food']
        if self.food >= self.food_required:
            self.population += 1
            self.food = 0
            self.food_required += 5
            print(f"{self.name} grew to population {self.population}!")
            if notification_sound:
                notification_sound.play()

        # Process production queue
        if self.production_queue:
            item = self.production_queue[0]
            cost = PRODUCTION_COSTS[item]
            self.production_progress += self.yields['Production']
            if self.production_progress >= cost:
                self.production_progress = 0
                self.production_queue.pop(0)
                self.complete_production(item)
        else:
            print(f"{self.name} is idle.")

    def complete_production(self, item):
        if item in UNIT_STATS:
            new_unit = Unit(self.x, self.y, self.owner, item)
            self.owner.units.append(new_unit)
            self.owner.game_map.tiles[self.y][self.x].unit = new_unit
            print(f"{item} produced in {self.name}!")
            if production_complete_sound:
                production_complete_sound.play()
        elif item in BUILDINGS:
            print(f"{item} constructed in {self.name}!")
            # Apply building effects (not implemented)
            if production_complete_sound:
                production_complete_sound.play()

    def change_production(self, item):
        if self.owner.resources['Gold'] >= PRODUCTION_COSTS.get(item, 0):
            self.production_queue.append(item)
            self.production_progress = 0
            self.owner.resources['Gold'] -= PRODUCTION_COSTS.get(item, 0)
            print(f"{item} added to production queue in {self.name}")
            if click_sound:
                click_sound.play()
        else:
            print("Not enough Gold to produce this item.")

# Tile Class
class Tile:
    def __init__(self, x, y, terrain_type):
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.terrain_type = terrain_type
        self.unit = None
        self.city = None
        self.improvement = None
        self.highlight = False

    def draw(self, surface):
        # Choose color based on terrain
        if self.terrain_type == 'Plains':
            color = GREEN
        elif self.terrain_type == 'Water':
            color = BLUE
        elif self.terrain_type == 'Mountain':
            color = GRAY
        elif self.terrain_type == 'Forest':
            color = DARK_GRAY
        else:
            color = BROWN

        pygame.draw.rect(surface, color, self.rect)

        # Highlight if selected
        if self.highlight:
            pygame.draw.rect(surface, YELLOW, self.rect, 3)

        # Draw improvements
        if self.improvement:
            image = IMAGES.get(self.improvement, None)
            if image:
                surface.blit(image, self.rect)

        # Draw city
        if self.city:
            image = IMAGES.get('City', None)
            if image:
                surface.blit(image, self.rect)

        # Draw unit
        if self.unit:
            image = IMAGES.get(self.unit.unit_type, None)
            if image:
                surface.blit(image, self.rect)

# GameMap Class
class GameMap:
    def __init__(self):
        self.tiles = self.generate_map()

    def generate_map(self):
        tiles = []
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                terrain = random.choices(
                    ['Plains', 'Water', 'Mountain', 'Forest'],
                    weights=[60, 10, 10, 20],
                    k=1
                )[0]
                tile = Tile(x, y, terrain)
                row.append(tile)
            tiles.append(row)
        return tiles

    def draw(self, surface):
        for row in self.tiles:
            for tile in row:
                tile.draw(surface)

# Player Class
class Player:
    def __init__(self, name, game_map):
        self.name = name
        self.units = []
        self.cities = []
        self.game_map = game_map
        self.selected_unit = None
        self.selected_city = None
        self.technology = Technology()
        self.show_research_menu = False
        self.show_city_menu = False
        self.resources = {'Gold': 20}  # Starting Gold

        # Starting unit
        start_x, start_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        starting_unit = Unit(start_x, start_y, self, 'Settler')
        self.units.append(starting_unit)
        game_map.tiles[start_y][start_x].unit = starting_unit

    def end_turn(self):
        for unit in self.units[:]:
            unit.reset_moves()
        for city in self.cities:
            city.produce()
        self.technology.advance_research()
        # Simple Gold generation based on number of cities
        self.resources['Gold'] += len(self.cities)
        print(f"Gold increased to {self.resources['Gold']}")
        if notification_sound:
            notification_sound.play()

    def start_research(self):
        self.show_research_menu = True
        if click_sound:
            click_sound.play()

# Game Class
class Game:
    def __init__(self):
        self.game_map = GameMap()
        self.player = Player("Player", self.game_map)
        self.running = True
        self.current_turn = 1

        # Create main buttons
        self.main_buttons = []
        self.create_main_buttons()

        # Create lists for menu buttons
        self.research_buttons = []
        self.city_buttons = []

    def create_main_buttons(self):
        button_width = BUTTON_WIDTH
        button_height = BUTTON_HEIGHT
        padding = 10
        x = WIDTH - button_width - padding
        y = padding

        # End Turn button
        end_turn_button = Button("End Turn", x, y, button_width, button_height, self.end_turn)
        self.main_buttons.append(end_turn_button)
        y += button_height + padding

        # Found City button
        found_city_button = Button("Found City", x, y, button_width, button_height, self.found_city)
        self.main_buttons.append(found_city_button)
        y += button_height + padding

        # Build Improvement button
        build_improvement_button = Button("Build Improvement", x, y, button_width, button_height, self.build_improvement)
        self.main_buttons.append(build_improvement_button)
        y += button_height + padding

        # City Management button
        city_management_button = Button("City Management", x, y, button_width, button_height, self.city_management)
        self.main_buttons.append(city_management_button)
        y += button_height + padding

        # Research button
        research_button = Button("Research", x, y, button_width, button_height, self.player.start_research)
        self.main_buttons.append(research_button)
        y += button_height + padding

    def end_turn(self):
        self.player.end_turn()
        self.current_turn += 1
        print(f"Turn {self.current_turn} started.")
        if click_sound:
            click_sound.play()

    def found_city(self):
        if self.player.selected_unit and self.player.selected_unit.unit_type == 'Settler':
            self.player.selected_unit.found_city(self.game_map)
        else:
            print("No settler unit selected.")

    def build_improvement(self):
        if self.player.selected_unit and self.player.selected_unit.unit_type == 'Worker':
            self.player.selected_unit.build_improvement(self.game_map)
        else:
            print("No worker unit selected.")

    def city_management(self):
        if self.player.selected_city:
            self.player.show_city_menu = True
            if click_sound:
                click_sound.play()
        else:
            print("No city selected.")

    def game_loop(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    pos = event.pos
                    self.handle_main_button_click(event, pos)
                    self.handle_menu_button_click(event, pos)
                    self.handle_tile_click(pos)

            elif event.type == pygame.KEYDOWN:
                if self.player.show_research_menu:
                    self.handle_research_input(event.key)
                if self.player.show_city_menu:
                    self.handle_city_input(event.key)

    def handle_main_button_click(self, event, pos):
        for button in self.main_buttons:
            button.handle_event(event, pos)

    def handle_menu_button_click(self, event, pos):
        if self.player.show_research_menu:
            for button in self.research_buttons:
                button.handle_event(event, pos)
        if self.player.show_city_menu:
            for button in self.city_buttons:
                button.handle_event(event, pos)

    def handle_tile_click(self, pos):
        x, y = pos[0] // TILE_SIZE, pos[1] // TILE_SIZE
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            tile = self.game_map.tiles[y][x]
            if self.player.show_city_menu or self.player.show_research_menu:
                # Ignore tile clicks when in management menus
                return
            # Select unit
            if tile.unit and tile.unit.owner == self.player:
                self.player.selected_unit = tile.unit
                self.player.selected_city = None
                self.clear_highlights()
                tile.highlight = True
                print(f"Unit selected at ({x}, {y})")
            # Select city
            elif tile.city and tile.city.owner == self.player:
                self.player.selected_city = tile.city
                self.player.selected_unit = None
                self.clear_highlights()
                tile.highlight = True
                print(f"City selected at ({x}, {y})")
            elif self.player.selected_unit:
                # Move unit
                dx = x - self.player.selected_unit.x
                dy = y - self.player.selected_unit.y
                if abs(dx) + abs(dy) == 1 and self.player.selected_unit.moves > 0:
                    self.player.selected_unit.move_unit(dx, dy, self.game_map)
                    self.clear_highlights()
                else:
                    print("Invalid move.")
            else:
                print("No unit or city selected.")

    def clear_highlights(self):
        for row in self.game_map.tiles:
            for tile in row:
                tile.highlight = False

    def update(self):
        pass  # Future game logic updates

    def draw(self):
        window.fill(BLACK)
        self.game_map.draw(window)
        self.draw_ui()
        if self.player.show_research_menu:
            self.draw_research_menu()
        if self.player.show_city_menu:
            self.draw_city_menu()
        pygame.display.flip()

    def draw_ui(self):
        # Draw main buttons
        for button in self.main_buttons:
            button.draw(window)

        # Display current turn and resources
        font = pygame.font.SysFont(None, 24)
        turn_text = font.render(f"Turn: {self.current_turn}", True, WHITE)
        window.blit(turn_text, (10, 10))

        # Display player's resources
        resources_text = f"Gold: {self.player.resources['Gold']}"
        resources_surf = font.render(resources_text, True, WHITE)
        window.blit(resources_surf, (10, 40))

        # Display selected unit or city information
        if self.player.selected_unit:
            info_text = f"Selected Unit: {self.player.selected_unit.unit_type} (Moves left: {self.player.selected_unit.moves})"
            info_surf = font.render(info_text, True, WHITE)
            window.blit(info_surf, (10, 70))
        elif self.player.selected_city:
            info_text = f"Selected City: {self.player.selected_city.name} (Population: {self.player.selected_city.population})"
            info_surf = font.render(info_text, True, WHITE)
            window.blit(info_surf, (10, 70))

    def draw_research_menu(self):
        font = pygame.font.SysFont(None, 24)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent overlay
        window.blit(overlay, (0, 0))

        available_techs = self.player.technology.get_available_techs()
        title_text = font.render("Choose a technology to research:", True, WHITE)
        window.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))

        # Create buttons for each available technology
        button_width = 200
        button_height = 50
        padding = 20
        start_x = WIDTH//2 - (button_width + padding) // 2
        start_y = 100

        self.research_buttons = []

        for idx, tech in enumerate(available_techs):
            icon_key = f"research_{tech.lower().replace(' ', '_')}_icon"
            icon = IMAGES.get(icon_key, None)
            button = Button(tech, WIDTH//2 - button_width//2, start_y + idx * (button_height + padding),
                            button_width, button_height, lambda t=tech: self.select_tech(t), icon=icon)
            self.research_buttons.append(button)
            button.draw(window)

        # Close Button
        close_button = Button("X", WIDTH//2 + button_width//2 - 40, 50, 30, 30, self.close_research_menu, icon=IMAGES.get('close_icon'))
        self.research_buttons.append(close_button)
        close_button.draw(window)

        # Display Research Progress Bar
        if self.player.technology.current_research:
            progress_bg = IMAGES.get('progress_bar_bg', None)
            progress_fill = IMAGES.get('progress_bar_fill', None)
            if progress_bg and progress_fill:
                window.blit(progress_bg, (WIDTH//2 - progress_bg.get_width()//2, start_y + len(available_techs) * (button_height + padding) + 30))
                # Calculate progress percentage
                current_tech = self.player.technology.current_research
                progress = self.player.technology.progress / self.player.technology.available_techs[current_tech]['cost']
                if progress > 1:
                    progress = 1
                # Scale the fill based on progress
                fill_width = int(progress_fill.get_width() * progress)
                fill_rect = pygame.Rect(WIDTH//2 - progress_fill.get_width()//2, start_y + len(available_techs) * (button_height + padding) + 30, fill_width, progress_fill.get_height())
                window.blit(progress_fill, fill_rect, area=pygame.Rect(0, 0, fill_width, progress_fill.get_height()))
            else:
                # Draw simple progress bar if images not available
                pygame.draw.rect(window, GRAY, (WIDTH//2 - 100, start_y + len(available_techs) * (button_height + padding) + 30, 200, 20))
                if self.player.technology.available_techs.get(self.player.technology.current_research, {}).get('cost', 1) > 0:
                    progress = self.player.technology.progress / self.player.technology.available_techs[self.player.technology.current_research]['cost']
                    fill_width = int(200 * progress)
                    pygame.draw.rect(window, BLUE, (WIDTH//2 - 100, start_y + len(available_techs) * (button_height + padding) + 30, fill_width, 20))

    def close_research_menu(self):
        self.player.show_research_menu = False
        if click_sound:
            click_sound.play()

    def select_tech(self, tech_name):
        self.player.technology.start_research(tech_name)
        self.player.show_research_menu = False
        print(f"Researching {tech_name}")
        if click_sound:
            click_sound.play()

    def handle_research_input(self, key):
        pass  # Now handled via buttons

    def draw_city_menu(self):
        font = pygame.font.SysFont(None, 24)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent overlay
        window.blit(overlay, (0, 0))

        city = self.player.selected_city

        # Display city information
        info_lines = [
            f"City Management - {city.name}",
            f"Population: {city.population}",
            f"Food: {city.food}/{city.food_required}",
            f"Gold: {self.player.resources['Gold']}",
            "",
            "Choose a production option below:",
        ]

        for idx, line in enumerate(info_lines):
            text = font.render(line, True, WHITE)
            window.blit(text, (WIDTH//2 - text.get_width()//2, 50 + idx * 30))

        # Create buttons for production options
        button_width = 200
        button_height = 50
        padding = 20
        start_x = WIDTH//2 - (button_width + padding) // 2
        start_y = 150

        self.city_buttons = []

        production_options = ['Settler', 'Worker', 'Warrior', 'Granary', 'Monument']
        for idx, item in enumerate(production_options):
            icon_key = f"production_{item.lower()}_icon"
            icon = IMAGES.get(icon_key, None)
            button = Button(item, WIDTH//2 - button_width//2, start_y + idx * (button_height + padding),
                            button_width, button_height, lambda i=item: self.select_production(i), icon=icon)
            self.city_buttons.append(button)
            button.draw(window)

        # Close Button
        close_button = Button("X", WIDTH//2 + button_width//2 - 40, 50, 30, 30, self.close_city_menu, icon=IMAGES.get('close_icon'))
        self.city_buttons.append(close_button)
        close_button.draw(window)

        # Display Production Progress Bar
        if city.production_queue:
            progress_bg = IMAGES.get('progress_bar_bg', None)
            progress_fill = IMAGES.get('progress_bar_fill', None)
            if progress_bg and progress_fill:
                window.blit(progress_bg, (WIDTH//2 - progress_bg.get_width()//2, start_y + len(production_options) * (button_height + padding) + 30))
                # Calculate progress percentage
                current_item = city.production_queue[0]
                progress = city.production_progress / PRODUCTION_COSTS[current_item]
                if progress > 1:
                    progress = 1
                # Scale the fill based on progress
                fill_width = int(progress_fill.get_width() * progress)
                fill_rect = pygame.Rect(WIDTH//2 - progress_fill.get_width()//2, start_y + len(production_options) * (button_height + padding) + 30, fill_width, progress_fill.get_height())
                window.blit(progress_fill, fill_rect, area=pygame.Rect(0, 0, fill_width, progress_fill.get_height()))
            else:
                # Draw simple progress bar if images not available
                pygame.draw.rect(window, GRAY, (WIDTH//2 - 100, start_y + len(production_options) * (button_height + padding) + 30, 200, 20))
                if PRODUCTION_COSTS.get(city.production_queue[0], 0) > 0:
                    progress = city.production_progress / PRODUCTION_COSTS[city.production_queue[0]]
                    fill_width = int(200 * progress)
                    pygame.draw.rect(window, GREEN, (WIDTH//2 - 100, start_y + len(production_options) * (button_height + padding) + 30, fill_width, 20))

    def close_city_menu(self):
        self.player.show_city_menu = False
        if click_sound:
            click_sound.play()

    def select_production(self, item):
        city = self.player.selected_city
        if self.player.resources['Gold'] >= PRODUCTION_COSTS.get(item, 0):
            city.change_production(item)
            print(f"{item} added to production queue in {city.name}")
        else:
            print("Not enough Gold to produce this item.")
        if click_sound:
            click_sound.play()

    def handle_city_input(self, key):
        pass  # Now handled via buttons

# Main Execution
if __name__ == "__main__":
    game = Game()
    game.game_loop()
