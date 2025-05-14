import pygame
import sys
import random
import math
import os
from random import randint, choice

# Initialize pygame
pygame.init()
pygame.mixer.init()


# Load and play background music in a loop
pygame.mixer.music.load("bg.mp3")  
pygame.mixer.music.set_volume(0.5)  
pygame.mixer.music.play(-1)


# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DJONG Ultimate")

# Classic Arcade Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
PURPLE = (150, 50, 255)
ORANGE = (255, 150, 50)

# Game variables
clock = pygame.time.Clock()
FPS = 90
font = pygame.font.SysFont('Arial', 30, bold=True)
big_font = pygame.font.SysFont('Arial', 60, bold=True)
title_font = pygame.font.SysFont('Impact', 80)
points_to_win = 5
last_change_time = 0
change_delay = 200  # milliseconds
crazy_mode = False
ball_size_changes = True
bs = 20  # Initial ball size

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
game_state = MENU

# Game modes
SINGLE_PLAYER = 0
MULTI_PLAYER = 1
game_mode = None

# Difficulty levels
EASY = 0
MODERATE = 1
HARD = 2
difficulty = EASY
difficulty_colors = [WHITE, YELLOW, RED]


try:
    bg_img = pygame.image.load("g-img.jpg")
    bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
except:
    # Create retro gradient background if image not found
    bg_img = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        # Blue to purple gradient
        color = (50, 50, 100 + int(155 * y / HEIGHT))
        pygame.draw.line(bg_img, color, (0, y), (WIDTH, y))

try:
    pl_img = pygame.image.load("pl-img.jpg")
    pl_img = pygame.transform.scale(pl_img, (WIDTH, HEIGHT))
except:
    # Create classic game background if image not found
    pl_img = pygame.Surface((WIDTH, HEIGHT))
    pl_img.fill(BLACK)
    # Draw court lines
    pygame.draw.rect(pl_img, BLUE, (0, 0, WIDTH, HEIGHT), 10)
    for y in range(30, HEIGHT, 40):
        pygame.draw.rect(pl_img, WHITE, (WIDTH//2 - 2, y, 4, 20))


def resource_path(relative_path):
    """ Get absolute path to resource (for PyInstaller compatibility). """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

collision_sound = pygame.mixer.Sound(resource_path("collision.mp3"))

class Paddle:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, 15, 100)
        self.speed = 5
        self.score = 0
        self.color = color
    
    def move(self, up_key, down_key):
        keys = pygame.key.get_pressed()
        if keys[up_key] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[down_key] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
    
    def ai_move(self, ball, difficulty):
        if difficulty == EASY:
            if random.random() > 0.7:
                if ball.rect.centery < self.rect.centery and self.rect.top > 0:
                    self.rect.y -= self.speed * 0.7
                elif ball.rect.centery > self.rect.centery and self.rect.bottom < HEIGHT:
                    self.rect.y += self.speed * 0.7
        elif difficulty == MODERATE:
            if ball.rect.centery < self.rect.centery and self.rect.top > 0:
                self.rect.y -= self.speed * 0.9
            elif ball.rect.centery > self.rect.centery and self.rect.bottom < HEIGHT:
                self.rect.y += self.speed * 0.9
        else:  # HARD
            predicted_y = ball.rect.centery + (ball.dx * (self.rect.left - ball.rect.right) / ball.speed)
            predicted_y = max(50, min(predicted_y, HEIGHT - 50))
            
            if predicted_y < self.rect.centery and self.rect.top > 0:
                self.rect.y -= self.speed * 1.1
            elif predicted_y > self.rect.centery and self.rect.bottom < HEIGHT:
                self.rect.y += self.speed * 1.1
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - bs//2, HEIGHT // 2 - bs//2, bs, bs)
        self.dx = 5 * random.choice([-1, 1])
        self.dy = 5 * random.choice([-1, 1])
        self.speed = 5
        self.colors = [RED, GREEN, BLUE, YELLOW]
        self.current_color = RED
    
    def move(self):
        self.rect.x += self.dx * (1.5 if crazy_mode else 1)
        self.rect.y += self.dy * (1.5 if crazy_mode else 1)
        
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy *= -1
        
        if self.rect.left <= 0:
            return "right"
        if self.rect.right >= WIDTH:
            return "left"
        return None
    
    def draw(self):
        self.current_color = choice(self.colors) if crazy_mode else RED
        pygame.draw.ellipse(screen, self.current_color, self.rect)
        pygame.draw.ellipse(screen, WHITE, self.rect, 2)
    
    def reset(self):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.dx = 5 * random.choice([-1, 1])
        self.dy = 5 * random.choice([-1, 1])
        self.speed = 5
        self.rect.size = (bs, bs)
    
    def collide(self, paddle):
        if self.rect.colliderect(paddle.rect):
            relative_intersect = (paddle.rect.centery - self.rect.centery) / (paddle.rect.height / 2)
            bounce_angle = relative_intersect * (5 * 3.14159 / 12)
            
            self.speed = min(self.speed * 1.05, 12)
            self.dx = -self.dx
            self.dy = -self.speed * pygame.math.Vector2(1, 0).rotate(bounce_angle * 180 / 3.14159).y
            
            #paddle.color = (randint(0, 255), randint(0, 255), randint(0, 255))
            pygame.mixer.Sound.play(collision_sound) 
            return True
        return False

def draw_text(text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    screen.blit(text_surface, text_rect)

def draw_button(text, font, color, x, y, width, height, hover_color, action=None, selected=False):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    current_color = color
    border_color = WHITE
    
    if selected:
        current_color = hover_color
        border_color = YELLOW
    elif x < mouse[0] < x + width and y < mouse[1] < y + height:
        current_color = hover_color
    
    pygame.draw.rect(screen, current_color, (x, y, width, height))
    pygame.draw.rect(screen, border_color, (x, y, width, height), 3)
    
    draw_text(text, font, BLACK, x + width // 2, y + height // 2)
    
    if click[0] == 1 and x < mouse[0] < x + width and y < mouse[1] < y + height and action is not None:
        return action
    return None

def game_menu():
    global game_state, points_to_win, difficulty, last_change_time, game_mode, crazy_mode

    screen.blit(bg_img, (0, 0))

    # Title with retro effect
    draw_text("DJONG ULTIMATE", title_font, RED, WIDTH // 2 + 5, 105)
    draw_text("DJONG ULTIMATE", title_font, WHITE, WIDTH // 2, 100)
    
    # Points to win selector
    current_time = pygame.time.get_ticks()
    draw_text(f"POINTS TO WIN: {points_to_win}", font, WHITE, WIDTH // 2, 200)
    
    if draw_button("-", font, GREEN, WIDTH // 2 - 120, 230, 50, 50, YELLOW,"decrease") == "decrease" and current_time - last_change_time > change_delay:
        points_to_win = max(1, points_to_win - 1)
        last_change_time = current_time
    
    if draw_button("+", font, GREEN, WIDTH // 2 + 70, 230, 50, 50, YELLOW,"increase") == "increase" and current_time - last_change_time > change_delay:
        points_to_win = min(10, points_to_win + 1)
        last_change_time = current_time
 
    # Game mode selector
    draw_text("GAME MODE:", font, WHITE, WIDTH // 2, 300)
    single_action = draw_button("1 PLAYER", font, GREEN, WIDTH//2 - 150, 330, 140, 50, 
                              BLUE, "single", game_mode == SINGLE_PLAYER)
    multi_action = draw_button("2 PLAYERS", font, GREEN, WIDTH//2 + 10, 330, 140, 50, 
                             PURPLE, "multi", game_mode == MULTI_PLAYER)
    
    if single_action == "single":
        game_mode = SINGLE_PLAYER
    elif multi_action == "multi":
        game_mode = MULTI_PLAYER
    
    # Difficulty selector (only for single player)
    if game_mode == SINGLE_PLAYER:
        draw_text("DIFFICULTY:", font, WHITE, WIDTH // 2 , 440)
        easy_action = draw_button("EASY", font, GREEN, WIDTH//2 - 150, 470, 100, 50, 
                                difficulty_colors[EASY], "easy", difficulty == EASY)
        moderate_action = draw_button("NORMAL", font, GREEN, WIDTH//2 - 25, 470, 150, 50, 
                                    difficulty_colors[MODERATE], "moderate", difficulty == MODERATE)
        hard_action = draw_button("HARD", font, GREEN, WIDTH//2 + 175, 470, 100, 50, 
                                 difficulty_colors[HARD], "hard", difficulty == HARD)
            # Draw W/S movement instruction at the bottom
        move_text = font.render("You're left paddle.. Use W and S keys to move up and down", True, WHITE)
        screen.blit(move_text, (WIDTH // 2 - move_text.get_width() // 2, HEIGHT - 50))
        if easy_action == "easy":
            difficulty = EASY
        elif moderate_action == "moderate":
            difficulty = MODERATE
        elif hard_action == "hard":
            difficulty = HARD
    else:
            
        move_text = font.render("Left Paddle W(up), S(down) -- Right Paddle UPkey and DOWNkey ", True, WHITE)
        screen.blit(move_text, (WIDTH // 2 - move_text.get_width() // 2, HEIGHT - 50))
    

    move_text = font.render("Press B to Increase Ball Size and X to Reduce", True, WHITE)
    screen.blit(move_text, (310,680))
           

    
    # Start button
    if draw_button("START", big_font, GREEN, WIDTH // 2 - 100, 550, 200, 80, YELLOW, "start"):
        game_state = PLAYING
        return True
    pygame.draw.rect(screen, RED, (0, 0, WIDTH, HEIGHT), 10)
    return False

def game_over_screen(player_won):
    global game_state
    
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    if player_won:
        # Victory graffiti effect
        draw_text("VICTORY!", title_font, YELLOW, WIDTH // 2, HEIGHT // 2 - 80)
        draw_text("VICTORY!", title_font, ORANGE, WIDTH // 2 + 5, HEIGHT // 2 - 75)
        
        # Particle effect
        for _ in range(20):
            x = random.randint(WIDTH//2 - 100, WIDTH//2 + 100)
            y = random.randint(HEIGHT//2 - 50, HEIGHT//2 + 50)
            pygame.draw.circle(screen, YELLOW, (x, y), random.randint(2, 5))
    else:
        draw_text("GAME OVER", title_font, RED, WIDTH // 2, HEIGHT // 2 - 80)
        draw_text("TRY AGAIN!", font, WHITE, WIDTH // 2, HEIGHT // 2 - 20)
    
    # Restart button
    if draw_button("RESTART", font, GREEN, WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 60, YELLOW, "restart"):
        game_state = MENU
        return True
    
    # Quit button
    if draw_button("QUIT", font, RED, WIDTH // 2 - 100, HEIGHT // 2 + 180, 200, 60, ORANGE, "quit"):
        pygame.quit()
        sys.exit()
    
    return False

def main():
    global game_state, difficulty, crazy_mode, bs
    
    player = Paddle(20, HEIGHT // 2 - 50, GREEN)
    opponent = Paddle(WIDTH - 35, HEIGHT // 2 - 50, RED)
    ball = Ball()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b and ball_size_changes:
                    bs = min(50, bs * 2)
                    ball.rect.size = (bs, bs)
                if event.key == pygame.K_x and ball_size_changes:
                    bs = max(10, bs // 2)
                    ball.rect.size = (bs, bs)
        
        if game_state == MENU:
           
            screen.blit(bg_img, (0, 0))
            if game_menu():
                player = Paddle(20, HEIGHT // 2 - 50, GREEN)
                opponent = Paddle(WIDTH - 35, HEIGHT // 2 - 50, RED)
                ball = Ball()
        
        elif game_state == PLAYING:
         
            screen.blit(pl_img, (0, 0))

            # Player controls
            player.move(pygame.K_w, pygame.K_s)
            
            # Opponent controls
            if game_mode == SINGLE_PLAYER:
                opponent.ai_move(ball, difficulty)
            else:
                opponent.move(pygame.K_UP, pygame.K_DOWN)
            
            # Ball logic
            result = ball.move()
            if result == "left":
                player.score += 1
                ball.reset()
                if player.score >= points_to_win:
                    game_state = GAME_OVER
            elif result == "right":
                opponent.score += 1
                ball.reset()
                if opponent.score >= points_to_win:
                    game_state = GAME_OVER
            
            ball.collide(player)
            ball.collide(opponent)
            
            # Draw elements
            player.draw()
            opponent.draw()
            ball.draw()
            
            # Draw scores
            draw_text(f"{player.score}", big_font, GREEN, WIDTH // 4, 50)
            draw_text(f"{opponent.score}", big_font, RED, 3 * WIDTH // 4, 50)
        
        elif game_state == GAME_OVER:
            screen.blit(pl_img, (0, 0))
            player_won = player.score > opponent.score
            if game_over_screen(player_won):
                player = Paddle(20, HEIGHT // 2 - 50, GREEN)
                opponent = Paddle(WIDTH - 35, HEIGHT // 2 - 50, RED)
                ball = Ball()
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()