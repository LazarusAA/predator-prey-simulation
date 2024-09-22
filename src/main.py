from environment import Obstacle, FoodArea, HidingSpot
import pygame
import random
from agent import Agent, Prey, Predator
from collections import defaultdict
import numpy as np

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 1200, 800
SIMULATION_WIDTH = 900
SIMULATION_HEIGHT = 600  
CONTROL_PANEL_WIDTH = WIDTH - SIMULATION_WIDTH
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Emergent Ecosystem Simulation")

# Colors
BACKGROUND_COLOR = (240, 248, 255)  
SIMULATION_BORDER = (70, 130, 180)
PANEL_BACKGROUND = (230, 230, 250)
TEXT_COLOR = (47, 79, 79)
PREY_COLOR = (46, 139, 87)
PREDATOR_COLOR = (178, 34, 34)
OBSTACLE_COLOR = (119, 136, 153)
FOOD_AREA_COLOR = (154, 205, 50)
HIDING_SPOT_COLOR = (210, 180, 140)
BUTTON_COLOR = (176, 196, 222)
BUTTON_TEXT_COLOR = (25, 25, 112)
SLIDER_COLOR = (176, 196, 222)
SLIDER_HANDLE_COLOR = (70, 130, 180)  

# Create lists to store agents
prey_list = []
predator_list = []

# Initialize agents
NUM_PREY = 100  # Increased initial prey count
NUM_PREDATORS = 3  # Reduced initial predator count

for _ in range(NUM_PREY):
    x = random.randint(0, SIMULATION_WIDTH)
    y = random.randint(0, SIMULATION_HEIGHT)
    prey_list.append(Prey(x, y))

for _ in range(NUM_PREDATORS):
    x = random.randint(0, SIMULATION_WIDTH)
    y = random.randint(0, SIMULATION_HEIGHT)
    predator_list.append(Predator(x, y))

# Create lists to store environmental features
obstacles = []
food_areas = []
hiding_spots = []

# Initialize environmental features
NUM_OBSTACLES = 5  
NUM_FOOD_AREAS = 3  
NUM_HIDING_SPOTS = 3  

for _ in range(NUM_OBSTACLES):
    x = random.randint(50, SIMULATION_WIDTH - 50)
    y = random.randint(50, SIMULATION_HEIGHT - 50)
    radius = random.randint(20, 40)
    obstacles.append(Obstacle(x, y, radius))

for _ in range(NUM_FOOD_AREAS):
    x = random.randint(50, SIMULATION_WIDTH - 50)
    y = random.randint(50, SIMULATION_HEIGHT - 50)
    radius = random.randint(50, 80)
    food_areas.append(FoodArea(x, y, radius))

for _ in range(NUM_HIDING_SPOTS):
    x = random.randint(50, SIMULATION_WIDTH - 50)
    y = random.randint(50, SIMULATION_HEIGHT - 50)
    radius = random.randint(30, 60)
    hiding_spots.append(HidingSpot(x, y, radius))

# UI elements
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label

    def draw(self, screen):
        pygame.draw.rect(screen, SLIDER_COLOR, self.rect)
        pos = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.line(screen, SLIDER_HANDLE_COLOR, (pos, self.rect.y), (pos, self.rect.y + self.rect.height), 4)
        font = pygame.font.Font(None, 24)
        label = font.render(f"{self.label}: {self.value:.2f}", True, TEXT_COLOR)
        screen.blit(label, (self.rect.x, self.rect.y - 25))

    def update(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.value = (mouse_pos[0] - self.rect.x) / self.rect.width * (self.max_val - self.min_val) + self.min_val
            self.value = max(self.min_val, min(self.max_val, self.value))

class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect)
        font = pygame.font.Font(None, 24)
        text = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

# Create sliders
sliders = [
    Slider(SIMULATION_WIDTH + 20, 80, 260, 20, 0.005, 0.02, Prey.energy_decay_rate, "Prey Energy Decay"),
    Slider(SIMULATION_WIDTH + 20, 140, 260, 20, 0.05, 0.3, Prey.energy_gain_rate, "Prey Energy Gain"),
    Slider(SIMULATION_WIDTH + 20, 200, 260, 20, 0.01, 0.03, Predator.energy_decay_rate, "Predator Energy Decay"),
    Slider(SIMULATION_WIDTH + 20, 260, 260, 20, 20, 60, Predator.energy_gain_from_prey, "Predator Energy Gain"),
    Slider(SIMULATION_WIDTH + 20, 320, 260, 20, 3, 10, Predator.reproduction_threshold, "Predator Reproduction Threshold")
]

# Simulation control
paused = False

def toggle_pause():
    global paused, last_update_time
    paused = not paused
    if not paused:
        last_update_time = pygame.time.get_ticks()

def restart_simulation():
    global prey_list, predator_list, obstacles, food_areas, hiding_spots, elapsed_time, last_update_time
    prey_list = [Prey(random.randint(0, SIMULATION_WIDTH), random.randint(0, SIMULATION_HEIGHT)) for _ in range(NUM_PREY)]
    predator_list = [Predator(random.randint(0, SIMULATION_WIDTH), random.randint(0, SIMULATION_HEIGHT)) for _ in range(NUM_PREDATORS)]
    
    obstacles = []
    food_areas = []
    hiding_spots = []
    
    for _ in range(NUM_OBSTACLES):
        x = random.randint(50, SIMULATION_WIDTH - 50)
        y = random.randint(50, SIMULATION_HEIGHT - 50)
        radius = random.randint(20, 40)
        obstacles.append(Obstacle(x, y, radius))

    for _ in range(NUM_FOOD_AREAS):
        x = random.randint(50, SIMULATION_WIDTH - 50)
        y = random.randint(50, SIMULATION_HEIGHT - 50)
        radius = random.randint(50, 80)
        food_areas.append(FoodArea(x, y, radius))

    for _ in range(NUM_HIDING_SPOTS):
        x = random.randint(50, SIMULATION_WIDTH - 50)
        y = random.randint(50, SIMULATION_HEIGHT - 50)
        radius = random.randint(30, 60)
        hiding_spots.append(HidingSpot(x, y, radius))

    elapsed_time = 0
    last_update_time = pygame.time.get_ticks()

# Create buttons
buttons = [
    Button(SIMULATION_WIDTH + 20, 380, 120, 40, "Pause", toggle_pause),
    Button(SIMULATION_WIDTH + 150, 380, 120, 40, "Restart", restart_simulation)
]

# Add these new variables for statistics tracking
MAX_HISTORY = 500
prey_history = []
predator_history = []

# Add this function for spatial partitioning
def create_spatial_hash(agents, cell_size):
    spatial_hash = defaultdict(list)
    for agent in agents:
        cell_x = int(agent.position.x // cell_size)
        cell_y = int(agent.position.y // cell_size)
        spatial_hash[(cell_x, cell_y)].append(agent)
    return spatial_hash

CELL_SIZE = 50

start_time = 0
elapsed_time = 0
last_update_time = 0

# Main game loop
running = True
clock = pygame.time.Clock()
frame_count = 0

def draw_statistics(screen, font, prey_list, predator_list, prey_history, predator_history, elapsed_time):
    stats_height = HEIGHT - SIMULATION_HEIGHT
    pygame.draw.rect(screen, PANEL_BACKGROUND, (0, SIMULATION_HEIGHT, SIMULATION_WIDTH, stats_height))
    pygame.draw.line(screen, SIMULATION_BORDER, (0, SIMULATION_HEIGHT), (SIMULATION_WIDTH, SIMULATION_HEIGHT), 2)

    # Create columns
    col_width = SIMULATION_WIDTH // 3
    
    # Column 1: Population stats
    prey_count = len(prey_list)
    predator_count = len(predator_list)
    ratio = prey_count / predator_count if predator_count > 0 else float('inf')
    
    pop_title = font.render("Population", True, TEXT_COLOR)
    prey_text = font.render(f"Prey: {prey_count}", True, PREY_COLOR)
    predator_text = font.render(f"Predators: {predator_count}", True, PREDATOR_COLOR)
    ratio_text = font.render(f"Prey-Predator Ratio: {ratio:.2f}", True, TEXT_COLOR)
    
    screen.blit(pop_title, (20, HEIGHT - stats_height + 10))
    screen.blit(prey_text, (20, HEIGHT - stats_height + 40))
    screen.blit(predator_text, (20, HEIGHT - stats_height + 70))
    screen.blit(ratio_text, (20, HEIGHT - stats_height + 100))

    # Column 2: Energy levels
    avg_prey_energy = sum(prey.energy for prey in prey_list) / max(len(prey_list), 1)
    avg_predator_energy = sum(predator.energy for predator in predator_list) / max(len(predator_list), 1)
    
    energy_title = font.render("Average Energy", True, TEXT_COLOR)
    prey_energy_text = font.render(f"Prey: {avg_prey_energy:.2f}", True, PREY_COLOR)
    predator_energy_text = font.render(f"Predators: {avg_predator_energy:.2f}", True, PREDATOR_COLOR)
    
    screen.blit(energy_title, (col_width + 20, HEIGHT - stats_height + 10))
    screen.blit(prey_energy_text, (col_width + 20, HEIGHT - stats_height + 40))
    screen.blit(predator_energy_text, (col_width + 20, HEIGHT - stats_height + 70))

    # Column 3: Other stats
    avg_prey_lifespan = sum(prey.age for prey in prey_list) / max(len(prey_list), 1)
    avg_predator_lifespan = sum(predator.age for predator in predator_list) / max(len(predator_list), 1)
    time_text = font.render(f"Simulation Time: {elapsed_time / 1000:.2f} s", True, TEXT_COLOR)

    other_title = font.render("Other Statistics", True, TEXT_COLOR)
    lifespan_text = font.render(f"Avg Lifespan - Prey: {avg_prey_lifespan:.2f}", True, PREY_COLOR)
    predator_lifespan_text = font.render(f"Predators: {avg_predator_lifespan:.2f}", True, PREDATOR_COLOR)

    screen.blit(other_title, (2 * col_width + 20, HEIGHT - stats_height + 10))
    screen.blit(lifespan_text, (2 * col_width + 20, HEIGHT - stats_height + 40))
    screen.blit(predator_lifespan_text, (2 * col_width + 20, HEIGHT - stats_height + 70))
    screen.blit(time_text, (2 * col_width + 20, HEIGHT - stats_height + 100))

    # Draw vertical separators
    pygame.draw.line(screen, SIMULATION_BORDER, (col_width, HEIGHT - stats_height), (col_width, HEIGHT), 2)
    pygame.draw.line(screen, SIMULATION_BORDER, (2 * col_width, HEIGHT - stats_height), (2 * col_width, HEIGHT), 2)

    # Population trend indicators
    prey_trend = prey_history[-1] - prey_history[0] if len(prey_history) > 1 else 0
    predator_trend = predator_history[-1] - predator_history[0] if len(predator_history) > 1 else 0

    trend_size = 15
    prey_trend_color = PREY_COLOR if prey_trend > 0 else PREDATOR_COLOR if prey_trend < 0 else TEXT_COLOR
    predator_trend_color = PREY_COLOR if predator_trend > 0 else PREDATOR_COLOR if predator_trend < 0 else TEXT_COLOR

    pygame.draw.polygon(screen, prey_trend_color, 
                        [(col_width - 30, HEIGHT - stats_height + 45), 
                         (col_width - 20, HEIGHT - stats_height + 35), 
                         (col_width - 10, HEIGHT - stats_height + 45)] if prey_trend > 0 else
                        [(col_width - 30, HEIGHT - stats_height + 35), 
                         (col_width - 20, HEIGHT - stats_height + 45), 
                         (col_width - 10, HEIGHT - stats_height + 35)] if prey_trend < 0 else
                        [(col_width - 30, HEIGHT - stats_height + 40), 
                         (col_width - 20, HEIGHT - stats_height + 40), 
                         (col_width - 10, HEIGHT - stats_height + 40)])

    pygame.draw.polygon(screen, predator_trend_color, 
                        [(col_width - 30, HEIGHT - stats_height + 75), 
                         (col_width - 20, HEIGHT - stats_height + 65), 
                         (col_width - 10, HEIGHT - stats_height + 75)] if predator_trend > 0 else
                        [(col_width - 30, HEIGHT - stats_height + 65), 
                         (col_width - 20, HEIGHT - stats_height + 75), 
                         (col_width - 10, HEIGHT - stats_height + 65)] if predator_trend < 0 else
                        [(col_width - 30, HEIGHT - stats_height + 70), 
                         (col_width - 20, HEIGHT - stats_height + 70), 
                         (col_width - 10, HEIGHT - stats_height + 70)])

font = pygame.font.Font(None, 24)

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  
                for slider in sliders:
                    slider.update(event.pos)
                for button in buttons:
                    button.handle_event(event)
        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:  
                for slider in sliders:
                    slider.update(event.pos)

    if not paused:
        # Update elapsed time
        if last_update_time > 0:
            elapsed_time += current_time - last_update_time
        
        # Update simulation parameters
        Prey.energy_decay_rate = sliders[0].value
        Prey.energy_gain_rate = sliders[1].value
        Predator.energy_decay_rate = sliders[2].value
        Predator.energy_gain_from_prey = sliders[3].value
        Predator.reproduction_threshold = int(sliders[4].value)

        # Create spatial hash for agents
        spatial_hash_prey = create_spatial_hash(prey_list, CELL_SIZE)
        spatial_hash_predator = create_spatial_hash(predator_list, CELL_SIZE)

        # Update agents
        for prey in prey_list[:]:
            prey.update(prey_list, predator_list, SIMULATION_WIDTH, SIMULATION_HEIGHT, obstacles, food_areas, hiding_spots, spatial_hash_prey, spatial_hash_predator, CELL_SIZE)

        for predator in predator_list[:]:
            predator.update(prey_list, predator_list, SIMULATION_WIDTH, SIMULATION_HEIGHT, obstacles, food_areas, hiding_spots, spatial_hash_prey, spatial_hash_predator, CELL_SIZE)

        # Update statistics
        prey_history.append(len(prey_list))
        predator_history.append(len(predator_list))
        if len(prey_history) > MAX_HISTORY:
            prey_history.pop(0)
            predator_history.pop(0)

    last_update_time = current_time

    # Draw everything
    screen.fill(BACKGROUND_COLOR)
    
    # Draw simulation area
    pygame.draw.rect(screen, SIMULATION_BORDER, (0, 0, SIMULATION_WIDTH, SIMULATION_HEIGHT), 2)

    # Draw environmental features
    for obstacle in obstacles:
        obstacle.draw(screen)
    for food_area in food_areas:
        food_area.draw(screen)
    for hiding_spot in hiding_spots:
        hiding_spot.draw(screen)

    for prey in prey_list:
        prey.draw(screen)

    for predator in predator_list:
        predator.draw(screen)

    # Draw control panel
    pygame.draw.rect(screen, PANEL_BACKGROUND, (SIMULATION_WIDTH, 0, CONTROL_PANEL_WIDTH, HEIGHT))
    
    # Draw title
    font_large = pygame.font.Font(None, 36)
    title = font_large.render("Simulation Controls", True, TEXT_COLOR)
    screen.blit(title, (SIMULATION_WIDTH + 20, 30))

    # Draw sliders
    for slider in sliders:
        slider.draw(screen)

    # Draw buttons
    for button in buttons:
        button.draw(screen)

    # Display population counts and average energy levels
    font = pygame.font.Font(None, 24)
    
    # Prey stats
    pygame.draw.rect(screen, PREY_COLOR, (SIMULATION_WIDTH + 20, 440, 260, 70))
    prey_text = font.render(f"Prey: {len(prey_list)}", True, BACKGROUND_COLOR)
    screen.blit(prey_text, (SIMULATION_WIDTH + 30, 450))
    
    avg_prey_energy = sum(prey.energy for prey in prey_list) / len(prey_list) if prey_list else 0
    prey_energy_text = font.render(f"Avg Prey Energy: {avg_prey_energy:.2f}", True, BACKGROUND_COLOR)
    screen.blit(prey_energy_text, (SIMULATION_WIDTH + 30, 480))
    
    # Predator stats
    pygame.draw.rect(screen, PREDATOR_COLOR, (SIMULATION_WIDTH + 20, 520, 260, 70))
    predator_text = font.render(f"Predators: {len(predator_list)}", True, BACKGROUND_COLOR)
    screen.blit(predator_text, (SIMULATION_WIDTH + 30, 530))
    
    avg_predator_energy = sum(predator.energy for predator in predator_list) / len(predator_list) if predator_list else 0
    predator_energy_text = font.render(f"Avg Predator Energy: {avg_predator_energy:.2f}", True, BACKGROUND_COLOR)
    screen.blit(predator_energy_text, (SIMULATION_WIDTH + 30, 560))

    # Draw statistics
    draw_statistics(screen, font, prey_list, predator_list, prey_history, predator_history, elapsed_time)

    # Display paused status
    if paused:
        pause_text = font_large.render("PAUSED", True, PREDATOR_COLOR)
        text_rect = pause_text.get_rect(center=(SIMULATION_WIDTH // 2, SIMULATION_HEIGHT // 2))
        screen.blit(pause_text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()