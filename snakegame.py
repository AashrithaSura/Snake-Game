import pygame
import pygame.mixer
import random
import json
import os
import time
from enum import Enum
from pathlib import Path

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Define Enums
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    SETTINGS = 3
    LEADERBOARD = 4
    GAME_OVER = 5
    ACHIEVEMENTS = 6

class GameMode(Enum):
    CLASSIC = 1
    TIME_TRIAL = 2
    OBSTACLES = 3

class PowerUpType(Enum):
    SPEED = 1
    DOUBLE_SCORE = 2
    SHIELD = 3

# Define Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Define Classes
class PowerUp:
    def __init__(self, type, position):
        self.type = type
        self.position = position
        self.duration = 5
        self.start_time = None
        self.active = False
        self.color = self.get_color()
    
    def get_color(self):
        colors = {
            PowerUpType.SPEED: BLUE,
            PowerUpType.DOUBLE_SCORE: YELLOW,
            PowerUpType.SHIELD: PURPLE
        }
        return colors.get(self.type, WHITE)

    def activate(self):
        self.active = True
        self.start_time = time.time()

    def is_expired(self):
        if not self.active:
            return False
        return time.time() - self.start_time > self.duration

class Achievement:
    def __init__(self, name, description, condition):
        self.name = name
        self.description = description
        self.unlocked = False
        self.condition = condition

class Settings:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.snake_block = 20
        self.snake_speed = 15
        self.difficulty = "Normal"
        self.fps = 60
        self.game_mode = GameMode.CLASSIC
        
        self.load_settings()

    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                try:
                    data = json.load(f)
                    self.snake_speed = data.get('speed', 15)
                    self.difficulty = data.get('difficulty', "Normal")
                    self.game_mode = GameMode[data.get('game_mode', "CLASSIC")]
                except:
                    pass

    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump({
                'speed': self.snake_speed,
                'difficulty': self.difficulty,
                'game_mode': self.game_mode.name
            }, f)

class Game:
    def __init__(self):
        # Basic setup
        self.settings = Settings()
        self.width = self.settings.width
        self.height = self.settings.height
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        
        # Initialize state and scores
        self.state = GameState.MENU
        self.scores = self.load_scores()
        self.current_score = 0
        
        # Game mode specific variables
        self.time_remaining = 60
        self.obstacles = []
        self.game_start_time = None
        
        # Power-up system
        self.current_power_up = None
        self.active_power_ups = []
        self.power_up_spawn_timer = 0
        self.power_up_spawn_interval = 10
        
        # Achievement system
        self.achievements = self.initialize_achievements()
        
        # Clock and font setup
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 50)
        self.small_font = pygame.font.SysFont(None, 30)
        
        # Text setup
        self.title_text = self.font.render("SNAKE GAME", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(self.width/2, 100))
        self.game_over_text = self.font.render("GAME OVER!", True, RED)
        self.game_over_rect = self.game_over_text.get_rect(center=(self.width/2, self.height/4))
        
        # Load sounds
        self.load_sounds()
        
        # Initialize game state
        self.reset_game ()

    def load_sounds(self):
        try:
            sound_dir = Path("C:\\Users\\suraa\\.vscode\\.vscode\\assets")
            self.eat_sound = pygame.mixer.Sound("C:\\Users\\suraa\\.vscode\\.vscode\\assets\\eat.wav")
            self.die_sound = pygame.mixer.Sound("C:\\Users\\suraa\\.vscode\\.vscode\\assets\\die.wav")
            self.highscore_sound = pygame.mixer.Sound("C:\\Users\\suraa\\.vscode\\.vscode\\assets\\highscore.wav")
            
            # Set volume
            self.eat_sound.set_volume(0.75)
            self.die_sound.set_volume(0.75)
            self.highscore_sound.set_volume(0.75)
            print("Sound files loaded successfully")
        except Exception as e:
            print(f"Warning: Sound files not found - {str(e)}")
            self.eat_sound = None
            self.die_sound = None
            self.highscore_sound = None

    def initialize_achievements(self):
        return {
            'Speed Demon': Achievement('Speed Demon', 'Score 100 points in under 60 seconds', 
                                    lambda score, time: score >= 100 and time <= 60),
            'Snake Master': Achievement('Snake Master', 'Reach a length of 20', 
                                     lambda length: length >= 20),
            'Power Player': Achievement('Power Player', 'Collect 5 power-ups', 
                                     lambda power_ups: power_ups >= 5),
            'High Scorer': Achievement('High Scorer', 'Score 500 points', 
                                    lambda score: score >= 500)
        }

    def load_scores(self):
        if os.path.exists('scores.json'):
            with open('scores.json', 'r') as f:
                try:
                    scores = json.load(f)
                    return scores if isinstance(scores, list) else []
                except:
                    return []
        return []

    def save_score(self, score):
        if not isinstance(self.scores, list):
            self.scores = []
        
        is_high_score = not self.scores or score > max(self.scores)
        
        self.scores.append(score)
        self.scores.sort(reverse=True)
        self.scores = self.scores[:10]
        
        if is_high_score and self.highscore_sound:
            try:
                self.highscore_sound.play()
            except:
                print("Error playing highscore sound")
        
        with open('scores.json', 'w') as f:
            json.dump(self.scores, f)

    def draw_leaderboard(self):
        self.window.fill(BLACK)
        self.draw_text("LEADERBOARD", GREEN, self.width/2, 50)
        
        if not self.scores:
            self.draw_text("No scores yet!", WHITE, self.width/2, self.height/2)
        else:
            for i, score in enumerate(self.scores[:10]):
                self.draw_text(f"#{i+1}: {score}", WHITE, self.width/2, 150 + i*40)
        
        self.draw_text("Press BACKSPACE to return", WHITE, self.width/2, 550)
        pygame.display.flip()

    def draw_text(self, text, color, x, y):
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        self.window.blit(text_surface, text_rect)

    def wrap_position(self, pos, bound):
        if pos >= bound:
            return 0
        elif pos < 0:
            return bound - self.settings.snake_block
        return pos

    def draw_snake(self):
        for x in self.snake_list:
            pygame.draw.rect(self.window, GREEN, [x[0], x[1], 
                                                self.settings.snake_block, 
                                                self.settings.snake_block])

    def handle_time_trial(self):
        if self.game_start_time is None:
            self.game_start_time = time.time()
        
        elapsed_time = time.time() - self.game_start_time
        remaining_time = max(0, self.time_remaining - elapsed_time)
        
        if remaining_time <= 0:
            self.save_score(self.current_score)
            self.state = GameState.GAME_OVER
            return True
        
        self.draw_text(f"Time: {int(remaining_time)}s", WHITE, self.width - 70, 20)
        return False

    def generate_obstacles(self):
        self.obstacles = []
        for _ in range(5):
            x = round(random.randrange(0, self.width - self.settings.snake_block) / 20.0) * 20.0
            y = round(random.randrange(0, self.height - self.settings.snake_block) / 20.0) * 20.0
            self.obstacles.append((x, y))

    def draw_obstacles(self ):
        for obstacle in self.obstacles:
            pygame.draw.rect(self.window, GRAY, 
                           [obstacle[0], obstacle[1], 
                            self.settings.snake_block, self.settings.snake_block])

    def check_obstacle_collision(self):
        for obstacle in self.obstacles:
            if abs(self.x1 - obstacle[0]) < self.settings .snake_block and \
               abs(self.y1 - obstacle[1]) < self.settings.snake_block:
                return True
        return False

    def handle_game(self):
        if self.game_start_time is None:
            self.game_start_time = time.time()

        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] and self.x1_change <= 0:
            self.x1_change = -self.settings.snake_block
            self.y1_change = 0
        elif keys[pygame.K_RIGHT] and self.x1_change >= 0:
            self.x1_change = self.settings.snake_block
            self.y1_change = 0
        elif keys[pygame.K_UP] and self.y1_change <= 0:
            self.y1_change = -self.settings.snake_block
            self.x1_change = 0
        elif keys[pygame.K_DOWN] and self.y1_change >= 0:
            self.y1_change = self.settings.snake_block
            self.x1_change = 0

        self.x1 = self.wrap_position(self.x1 + self.x1_change, self.width)
        self.y1 = self.wrap_position(self.y1 + self.y1_change, self.height)

        self.window.fill(BLACK)
        
        if self.settings.game_mode == GameMode.TIME_TRIAL:
            if self.handle_time_trial():
                return
        elif self.settings.game_mode == GameMode.OBSTACLES:
            self.draw_obstacles()
            if self.check_obstacle_collision():
                if not any(p.type == PowerUpType.SHIELD and p.active for p in self.active_power_ups):
                    if self.die_sound:
                        try:
                            self.die_sound.play()
                        except:
                            print("Error playing die sound")
                    self.save_score(self.current_score)
                    self.state = GameState.GAME_OVER
                    return

        pygame.draw.rect(self.window, RED, [self.foodx, self.foody, 
                                          self.settings.snake_block, self.settings.snake_block])
        self.handle_power_ups()

        snake_head = [self.x1, self.y1]
        self.snake_list.append(snake_head)

        if len(self.snake_list) > self.length_of_snake:
            del self.snake_list[0]

        for segment in self.snake_list[:-1]:
            if segment == snake_head:
                if not any(p.type == PowerUpType.SHIELD and p.active for p in self.active_power_ups):
                    if self.die_sound:
                        try:
                            self.die_sound.play()
                        except:
                            print("Error playing die sound")
                    self.save_score(self.current_score)
                    self.state = GameState.GAME_OVER
                    return

        self.draw_snake()
        self.draw_text(f"Score: {self.current_score}", WHITE, 70, 20)

        if abs(self.x1 - self.foodx) < self.settings.snake_block and \
           abs(self.y1 - self.foody) < self.settings.snake_block:
            self.foodx = round(random.randrange(0, self.width - self.settings.snake_block) / 20.0) * 20.0
            self.foody = round(random.randrange(0, self.height - self.settings.snake_block) / 20.0) * 20.0
            self.length_of_snake += 1
            self.current_score += 10
            if self.eat_sound:
                try:
                    self.eat_sound.play()
                except:
                    print("Error playing eat sound")

        self.check_achievements()

        pygame.display.flip()
        self.clock.tick(self.settings.snake_speed)

    def draw_menu(self):
        self.window.fill(BLACK)
        menu_options = [
            "1. Play Game",
            "2. Settings",
            "3. Leaderboard",
            "4. Achievements",
            "5. Quit"
        ]
        
        self.window.blit(self.title_text, self.title_rect)
        
        for i, option in enumerate(menu_options):
            text = self.font.render(option, True, WHITE)
            text_rect = text.get_rect(center=(self.width/2, 250 + i*50))
            self.window.blit(text, text_rect)
        
        pygame.display.flip()

    def draw_game_mode_selection(self):
        self.window.fill(BLACK)
        self.draw_text("SELECT GAME MODE", GREEN, self.width/2, 100)
        
        mode_options = [
            "1. Classic Mode",
            "2. Time Trial",
            "3. Obstacles",
            "4. Back to Menu"
        ]
        
        for i, option in enumerate(mode_options):
            self.draw_text(option, WHITE, self.width/2, 250 + i*50)
        
        pygame.display.flip()

    def draw_settings(self):
        self.window.fill(BLACK)
        self.draw_text("SETTINGS", GREEN, self.width/ 2, 100)
        self.draw_text(f"Snake Speed: {self.settings.snake_speed}", WHITE, self.width/2, 250)
        self.draw_text(f"Game Mode: {self.settings.game_mode.name}", WHITE, self.width/2, 300)
        self.draw_text("Press UP/DOWN to adjust speed", WHITE, self.width/2, 350)
        self.draw_text("Press M to change game mode", WHITE, self.width/2, 400)
        self.draw_text("Press BACKSPACE to return", WHITE, self.width/2, 500)
        pygame.display.flip()

    def draw_achievements(self):
        self.window.fill(BLACK)
        self.draw_text("ACHIEVEMENTS", GREEN, self.width/2, 50)
        
        y_pos = 150
        for achievement in self.achievements.values():
            color = GREEN if achievement.unlocked else GRAY
            self.draw_text(f"{achievement.name}", color, self.width/2, y_pos)
            desc_surface = self.small_font.render(achievement.description, True, color)
            desc_rect = desc_surface.get_rect(center=(self.width/2, y_pos + 30))
            self.window.blit(desc_surface, desc_rect)
            y_pos += 80
        
        self.draw_text("Press BACKSPACE to return", WHITE, self.width/2, 550)
        pygame.display.flip()

    def reset_game(self):
        try:
            self.x1 = self.width / 2
            self.y1 = self.height / 2
            self.x1_change = 0
            self.y1_change = 0
            self.snake_list = []
            self.length_of_snake = 1
            self.foodx = round(random.randrange(0, self.width - self.settings.snake_block) / 20.0) * 20.0
            self.foody = round(random.randrange(0, self.height - self.settings.snake_block) / 20.0) * 20.0
            self.current_score = 0
            self.game_start_time = None
            self.power_up_spawn_timer = time.time()
            self.current_power_up = None
            self.active_power_ups = []
            
            if self.settings.game_mode == GameMode.OBSTACLES:
                self.generate_obstacles()
            elif self.settings.game_mode == GameMode.TIME_TRIAL:
                self.time_remaining = 60
        except Exception as e:
            print(f"Error in reset_game: {str(e)}")

    def handle_game_over(self):
        try:
            # Save score first
            self.save_score(self.current_score)
            
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.reset_game()
                            self.state = GameState.PLAYING
                            return
                        elif event.key == pygame.K_m:
                            self.state = GameState.MENU
                            return
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            quit()

                # Draw game over screen
                self.window.fill(BLACK)
                self.window.blit(self.game_over_text, self.game_over_rect)
                
                # Draw score
                self.draw_text(f"Final Score: {self.current_score}", WHITE, self.width/2, self.height/3)
                
                # Draw achievements
                unlocked_achievements = [ach for ach in self.achievements.values() if ach.unlocked]
                if unlocked_achievements:
                    y_pos = self.height/2.5
                    self.draw_text("Achievements Unlocked:", GREEN, self.width/2, y_pos)
                    for achievement in unlocked_achievements:
                        y_pos += 30
                        text = self.small_font.render(achievement.name, True, GREEN)
                        rect = text.get_rect(center=(self.width/2, y_pos))
                        self.window.blit(text, rect)
                
                # Draw instructions
                self.draw_text("Press SPACE to Play Again", WHITE, self.width/2, self.height/1.8)
                self.draw_text("Press M for Main Menu", WHITE, self.width/2, self.height/1.6)
                self.draw_text("Press ESC to Quit", WHITE, self.width/2, self.height/1.4)
                
                pygame.display.flip()
                self.clock.tick(15)
                
        except Exception as e:
            print(f"Error in handle_game_over: {str(e)}")


    def handle_power_ups(self):
        # Handle existing power-ups
        for power_up in self.active_power_ups[:]:
            if power_up.is_expired():
                self.active_power_ups.remove(power_up)
        
        # Spawn new power-up
        current_time = time.time()
        if (self.current_power_up is None and 
            current_time - self.power_up_spawn_timer > self.power_up_spawn_interval):
            
            # Random chance to spawn power-up
            if random.random() < 0.3:  # 30% chance
                power_up_type = random.choice(list(PowerUpType))
                x = round(random.randrange(0, self.width - self.settings.snake_block) / 20.0) * 20.0
                y = round(random.randrange(0, self.height - self.settings.snake_block) / 20.0) * 20.0
                self.current_power_up = PowerUp(power_up_type, (x, y))
        
        # Draw and check collision with current power-up
        if self.current_power_up:
            pygame.draw.rect(self.window, 
                           self.current_power_up.color,
                           [self.current_power_up.position[0],
                            self.current_power_up.position[1],
                            self.settings.snake_block,
                            self.settings.snake_block])
            
            if (abs(self.x1 - self.current_power_up.position[0]) < self.settings.snake_block and
                abs(self.y1 - self.current_power_up.position[1]) < self.settings.snake_block):
                
                self.current_power_up.activate()
                self.active_power_ups.append(self.current_power_up)
                self.current_power_up = None
                self.power_up_spawn_timer = time.time()

    def check_achievements(self):
        game_time = time.time() - self.game_start_time if self.game_start_time else 0
        
        # Check each achievement
        for achievement in self.achievements.values():
            if not achievement.unlocked:
                if achievement.name == 'Speed Demon':
                    if achievement.condition(self.current_score, game_time):
                        achievement.unlocked = True
                
                elif achievement.name == 'Snake Master':
                    if achievement.condition(self.length_of_snake):
                        achievement.unlocked = True
                
                elif achievement.name == 'Power Player':
                    collected_power_ups = len([p for p in self.active_power_ups if p.active])
                    if achievement.condition(collected_power_ups):
                        achievement.unlocked = True
                
                elif achievement.name == 'High Scorer':
                    if achievement.condition(self.current_score):
                        achievement.unlocked = True

    def run(self):
        running = True
        game_mode_selection = False
        
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if game_mode_selection:
                            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                                if event.key == pygame.K_1:
                                    self.settings.game_mode = GameMode.CLASSIC
                                elif event.key == pygame.K_2:
                                    self.settings.game_mode = GameMode.TIME_TRIAL
                                elif event.key == pygame.K_3:
                                    self.settings.game_mode = GameMode.OBSTACLES
                                game_mode_selection = False
                                self.reset_game()
                                self.state = GameState.PLAYING
                            elif event.key == pygame.K_4:
                                game_mode_selection = False
                        elif self.state == GameState.MENU:
                            if event.key == pygame.K_1:
                                game_mode_selection = True
                            elif event.key == pygame.K_2:
                                self.state = GameState.SETTINGS
                            elif event.key == pygame.K_3:
                                self.state = GameState.LEADERBOARD
                            elif event.key == pygame.K_4:
                                self.state = GameState.ACHIEVEMENTS
                            elif event.key == pygame.K_5:
                                running = False
                        elif self.state == GameState.SETTINGS:
                            if event.key == pygame.K_BACKSPACE:
                                self.settings.save_settings()
                                self.state = GameState.MENU
                            elif event.key == pygame.K_UP:
                                self.settings.snake_speed = min(30, self.settings.snake_speed + 1)
                            elif event.key == pygame.K_DOWN:
                                self.settings.snake_speed = max(5, self.settings.snake_speed - 1)
                            elif event.key == pygame.K_m:
                                game_mode_selection = True
                        elif self.state == GameState.LEADERBOARD:
                            if event.key == pygame.K_BACKSPACE:
                                self.state = GameState.MENU
                        elif self.state == GameState.ACHIEVEMENTS:
                            if event.key == pygame.K_BACKSPACE:
                                self.state = GameState.MENU
                        elif self.state == GameState.PLAYING:
                            if event.key == pygame.K_ESCAPE:
                                self.state = GameState.MENU

                if game_mode_selection:
                    self.draw_game_mode_selection()
                elif self.state == GameState.MENU:
                    self.draw_menu()
                elif self.state == GameState.PLAYING:
                    self.handle_game()
                elif self.state == GameState.SETTINGS:
                    self.draw_settings()
                elif self.state == GameState.LEADERBOARD:
                    self.draw_leaderboard()
                elif self.state == GameState.ACHIEVEMENTS:
                    self.draw_achievements()
                elif self.state == GameState.GAME_OVER:
                    self.handle_game_over()

                if self.state != GameState.PLAYING:
                    self.clock.tick(self.settings.fps)

        except Exception as e:
            print(f"Error in game loop: {str(e)}")
        finally:
            pygame.quit()

if __name__ == "__main__":
    print("Starting Snake Game...")
    try:
        game = Game()
        print("Game instance created successfully")
        game.run()
    except Exception as e:
        print(f"Error starting game: {str(e)}")