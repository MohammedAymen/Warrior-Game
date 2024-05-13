import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Set up the screen
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CELL_SIZE = 20
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // CELL_SIZE, SCREEN_HEIGHT // CELL_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Warrior Arena")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
background_image = pygame.image.load("game_background_1.png")
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))


# Load the grid
def load_grid():
    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    # Place obstacles (impassable cells)
    # Example: grid[2][3] = 1
    return grid


# Heuristic function (Manhattan distance)
def heuristic(node, target):
    return abs(node[0] - target[0]) + abs(node[1] - target[1])


# A* algorithm implementation
def astar(grid, start, end):
    open_set = [start]
    came_from = {}

    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}

    while open_set:
        current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        open_set.remove(current)
        for neighbor in [(current[0] + 1, current[1]), (current[0] - 1, current[1]), (current[0], current[1] + 1),
                         (current[0], current[1] - 1)]:
            if neighbor[0] < 0 or neighbor[0] >= GRID_WIDTH or neighbor[1] < 0 or neighbor[1] >= GRID_HEIGHT:
                continue
            if grid[neighbor[1]][neighbor[0]] == 1:
                continue
            tentative_g_score = g_score[current] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, end)
                if neighbor not in open_set:
                    open_set.append(neighbor)

    return None


# Warrior class
class Warrior(pygame.sprite.Sprite):
    def __init__(self, grid):
        super().__init__()
        self.animations = self.load_animations()
        self.current_animation = self.animations["stand"]
        self.frame_index = 0
        self.image = self.current_animation[0]  # Initial image
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = 2
        self.grid = grid
        self.health = 3
        self.score = 0
        self.attack_range = 50
        self.attack_cooldown = 0
        self.target_pos = self.rect.center
        self.ANGLE_RANGES = {
            "UP": (45, 135),
            "DOWN": (-135, -45),
            "LEFT": (135, -135),
            "RIGHT": (-45, 45),
            "UP_LEFT": (90, 180),
            "UP_RIGHT": (0, 90),
            "DOWN_LEFT": (-180, -90),
            "DOWN_RIGHT": (-90, 0)
        }
        self.ATTACK_RANGE = 100
        self.action = "stand"
        self.is_hurting = False
        self.is_dying = False
        self.is_attacking = False
        self.frame_delay = 5
        self.frame_counter = 0
        self.is_walking = False  # Flag to indicate if the character is walking
        self.walk_stop_counter = 0
        self.hurt_cooldown = 0
        self.max_hurt_cooldown = 100  # Adjust as needed
        self.is_hurt = False
        self.is_animating = False

    

    def load_animations(self):
        animations = {}
        animations["stand"] = self.load_frames_from_folder(
            "./Warrior_clothes_2/Idle")
        animations["walk"] = self.load_frames_from_folder(
            "./Warrior_clothes_2/Run")
        animations["attack"] = self.load_frames_from_folder(
            "./Warrior_clothes_2/Attack_1")
        animations["hurt"] = self.load_frames_from_folder(
            "./Warrior_clothes_2/Hurt")
        animations["die"] = self.load_frames_from_folder(
            "./Warrior_clothes_2/Died")
        return animations

    def load_frames_from_folder(self, folder_path):
        frames = []
        for filename in os.listdir(folder_path):
            frame_path = os.path.join(folder_path, filename)
            if os.path.isfile(frame_path):
                frame = pygame.image.load(frame_path).convert_alpha()
                frame = pygame.transform.scale(frame, (120, 150))
                frames.append(frame)
        return frames

    def update(self, target_pos):
        if self.hurt_cooldown > 0:
            self.hurt_cooldown -= 1
        if self.is_dying:
            self.current_animation = self.animations["die"]
            self.is_dying=False
            self.frame_delay = 10
        elif self.is_hurting:
            self.current_animation = self.animations["hurt"]
            self.is_hurting=False
            self.frame_delay = 10
        elif self.is_attacking:
            self.current_animation = self.animations["attack"]
            self.frame_delay = 10 
        elif self.rect.center != self.target_pos:
            self.is_walking = True
            self.current_animation = self.animations["walk"]
            self.frame_delay = 5  # Adjust this value for the walking animation
        else:
            self.reset_animations()
            self.is_walking = False
            if not self.is_animating:
                self.current_animation=self.animations["stand"]
                self.frame_delay=10
        
        self.frame_counter += 1
        if self.frame_counter >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.current_animation)
            self.image.fill((0, 0, 0, 0))
            self.image.blit(self.current_animation[self.frame_index], (0, 0))  # Draw frame on top of previous frame
            self.frame_counter = 0
            self.reset_animations()
        if pygame.mouse.get_pressed()[0]:  # Check if left mouse button is pressed
            self.target_pos = target_pos  # Set target position to mouse position when clicked

        start_node = (self.rect.centerx // CELL_SIZE, self.rect.centery // CELL_SIZE)
        end_node = (self.target_pos[0] // CELL_SIZE, self.target_pos[1] // CELL_SIZE)
        path = astar(self.grid, start_node, end_node)

        if path:
            next_node = path[0]
            next_pos = (next_node[0] * CELL_SIZE + CELL_SIZE // 2, next_node[1] * CELL_SIZE + CELL_SIZE // 2)
            dx = next_pos[0] - self.rect.centerx
            dy = next_pos[1] - self.rect.centery
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist > self.speed:
                angle = math.atan2(dy, dx)
                self.rect.x += self.speed * math.cos(angle)
                self.rect.y += self.speed * math.sin(angle)
            else:
                # If close enough to the target position, move directly to it
                self.rect.center = next_pos

    def attack(self, enemies):
            self.is_attacking = True
            self.is_animating=True
            for enemy in enemies:
                if self.is_facing_enemy(enemy.rect.center):
                    # Calculate distance to enemy
                    distance_to_enemy = math.sqrt((enemy.rect.centerx - self.rect.centerx) ** 2 +
                                                  (enemy.rect.centery - self.rect.centery) ** 2)
                    if distance_to_enemy <= self.ATTACK_RANGE:
                        enemy.die(enemies) 
                        self.score += 1
              
        

    def is_facing_enemy(self, enemy_pos):
        warrior_angle = self.get_angle_to_mouse()
        for direction, angle_range in self.ANGLE_RANGES.items():
            if angle_range[0] <= warrior_angle <= angle_range[1]:
                return True
        return False

    def get_angle_to_mouse(self):
        dx = pygame.mouse.get_pos()[0] - self.rect.centerx
        dy = pygame.mouse.get_pos()[1] - self.rect.centery
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        return angle

    def hurt(self):
        if self.hurt_cooldown == 0 and not self.is_animating:
            self.health -= 1  # Decrease lives when hurt
            self.is_hurt = True
            self.is_animating=True
            self.hurt_cooldown = self.max_hurt_cooldown
            if self.health <= 0 :
                self.is_dying = True
                self.is_animating=True  # Set is_dying to True when lives run out
    
    def reset_animations(self):
        # Reset all animation flags
        self.is_walking = False
        self.is_hurting = False
        self.is_attacking = False
        self.is_dying = False
        self.is_animating = False

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, warrior):
        super().__init__()
        self.animations = self.load_animations()
        self.current_animation = self.animations["walk"]
        self.frame_index = 0
        self.image = self.current_animation[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.warrior = warrior
        self.action = "walk"
        self.attack_cooldown = 50
        self.max_attack_cooldown = 200
        self.is_attacking=False
        self.is_killed=False
        self.dying_animation_counter=0
        self.dying_animation_delay=10
        self.frame_counter=0
        self.frame_delay=5

    def load_animations(self):
        animations = {}
        animations["walk"] = self.load_frames_from_folder(
            "./PNG Sequences/Walking")
        animations["attack"] = self.load_frames_from_folder(
            "./PNG Sequences/Attacking")
        animations["die"] = self.load_frames_from_folder(
            "./PNG Sequences/Dying")
        return animations

    def load_frames_from_folder(self, folder_path):
        frames = []
        for filename in os.listdir(folder_path):
            frame_path = os.path.join(folder_path, filename)
            if os.path.isfile(frame_path):
                frame = pygame.image.load(frame_path).convert_alpha()
                frame = pygame.transform.scale(frame, (120, 150))
                frames.append(frame)
        return frames

    def update(self, target_pos,enemies):
        dx = self.warrior.rect.centerx - self.rect.centerx
        dy = self.warrior.rect.centery - self.rect.centery
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist > 25:
            self.current_animation = self.animations[self.action]
            angle = math.atan2(dy, dx)
            self.rect.x += self.speed * math.cos(angle)
            self.rect.y += self.speed * math.sin(angle)
        elif self.is_killed:
         # Perform dying animation
            self.current_animation = self.animations["die"]
            self.dying_animation_counter += 1
            if self.dying_animation_counter >= self.dying_animation_delay:
                # If delay is over, remove the enemy
                self.kill()
        else:
              self.current_animation = self.animations["attack"]
              self.attack(enemies) 
        # Update frame index
        self.frame_counter += 1
        if self.frame_counter >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.current_animation)
            self.image.fill((0, 0, 0, 0))
            self.image.blit(self.current_animation[self.frame_index], (0, 0))  # Draw frame on top of previous frame
            self.frame_counter = 0
            self.reset_animations()
        
       
        

    def attack(self,enemies):
        if self.attack_cooldown == 0:
            if self.warrior.is_attacking:
                # If warrior is attacking, remove enemy without dealing damage
                self.warrior.attack(enemies)
            elif self.rect.colliderect(self.warrior.rect) and not self.warrior.is_hurting:
                self.is_attacking=True
                self.warrior.hurt()
                self.attack_cooldown = self.max_attack_cooldown
        else:
            self.attack_cooldown -=1

    def die(self,enemies):
        self.is_killed=True

    def reset_animations(self):
        # Reset all animation flags
        self.is_walking = False
        self.is_killed= False
        self.is_attacking = False

# Main function
def main():
    # Load the grid
    grid = load_grid()

    # Create player and enemy groups
    all_sprites = pygame.sprite.Group()
    warriors = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    # Create warrior
    warrior = Warrior(grid)
    all_sprites.add(warrior)
    warriors.add(warrior)

    # Game loop
    heart_image = pygame.image.load('heart.png').convert_alpha()  # Load the heart image with alpha transparency
    heart_width, heart_height = 30, 30
    heart_image = pygame.transform.scale(heart_image, (heart_width, heart_height))
    
    start_button = pygame.Rect(300, 200, 200, 50)
    start_font = pygame.font.Font(None, 36)
    start_text = start_font.render("Start Game", True, WHITE)
    # Check if heart image is loaded successfully
    if heart_image is None:
        print("Error: Unable to load heart image")

    running = False
    target_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # Initialize target position
    enemy_spawn_rate = 0.01  # Initial enemy spawn rate
    enemy_speed = 1

    while True:  # Main menu loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    if start_button.collidepoint(mouse_pos):
                        running = True  # Start the game
        screen.blit(background_image, (0, 0))
        pygame.draw.rect(screen, RED, start_button)
        screen.blit(start_text, (start_button.x + 50, start_button.y + 10))
        pygame.display.flip()

        if running:
            break  # Exit the main menu loop and start the game

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return 
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    warrior.attack(enemies)
                   
                    
        # Update warrior position and facing direction based on mouse position
        screen.blit(background_image, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        # Draw pre-steps and X mark
        if warrior.is_walking:
            pygame.draw.line(screen, WHITE, warrior.rect.center, warrior.target_pos, 2)
            pygame.draw.circle(screen, WHITE, warrior.target_pos, 5)
        warrior.update(mouse_pos)

        # Handle warrior attacks
        enemy_attacking = False
        # Check collision between warrior and enemies
        for enemy in enemies:
            if warrior.rect.colliderect(enemy.rect):
                if warrior.is_facing_enemy(enemy.rect.center):
                  if enemy.is_attacking:
                    if not warrior.is_hurting:  # Make sure the warrior isn't already hurting
                            warrior.hurt()
                            enemy_attacking = True
                        
        if not enemy_attacking and warrior.health <= 0:
          print("Game Over")
          running = False
        # Update enemy movement
        for enemy in enemies:
            enemy.update(warrior.rect.center,enemies)
           # enemy.attack(enemies)
        # Spawning enemies
        if random.random() < enemy_spawn_rate:
            enemy = Enemy(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), enemy_speed, warrior)
            all_sprites.add(enemy)
            enemies.add(enemy)
        
       
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render("Score: " + str(warrior.score), True, WHITE)
        score_rect = score_text.get_rect()
        score_rect.topright = (SCREEN_WIDTH - 10, 10)  # Position score text on the top-right corner of the screen
        screen.blit(score_text, score_rect)

        # Draw hearts to represent warrior's health
        for i in range(warrior.health):
            heart_rect = heart_image.get_rect()
            screen.blit(heart_image, (10 + i * (heart_rect.width + 5), 10))

        # Draw all sprites
        all_sprites.draw(screen)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        pygame.time.Clock().tick(60)

    game_over_font = pygame.font.Font(None, 72)
    game_over_text = game_over_font.render("Game Over", True, WHITE)
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(game_over_text, game_over_rect)
    pygame.display.flip()

    replay = True
    while replay:
        for event in pygame.event.get():
         if event.type == pygame.QUIT:
            pygame.quit()
            return
         elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                if start_button.collidepoint(mouse_pos):
                    replay = False  # Exit replay loop
                    main()  # Start the game again

    # Quit Pygame
    pygame.quit()


if __name__ == "__main__":
    main()
