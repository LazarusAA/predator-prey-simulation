from environment import Obstacle, FoodArea, HidingSpot
import pygame
import random
import math

class Agent:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.acceleration = pygame.Vector2(0, 0)
        self.max_speed = 2
        self.max_speed_squared = 4
        self.max_force = 0.05
        self.perception_radius = 75
        self.perception_radius_squared = 5625
        self.energy = 150
        self.max_energy = 300
        self.radius = 5
        self.age = 0

    def update(self, width, height):
        self.velocity += self.acceleration
        if self.velocity.length_squared() > self.max_speed_squared:
            self.velocity.scale_to_length(self.max_speed)
        self.position += self.velocity
        self.acceleration *= 0
        self.wrap(width, height)
        self.age += 1

    def wrap(self, width, height):
        self.position.x %= width
        self.position.y %= height

    def seek(self, target):
        desired = target - self.position
        if desired.length_squared() > 0:
            desired.scale_to_length(self.max_speed)
            steer = desired - self.velocity
            return self.limit_force(steer)
        return pygame.Vector2(0, 0)

    def limit_force(self, force):
        if force.length_squared() > self.max_force * self.max_force:
            force.scale_to_length(self.max_force)
        return force

    def avoid_obstacle(self, obstacle):
        to_obstacle = obstacle.position - self.position
        distance_squared = to_obstacle.length_squared()
        if distance_squared < (obstacle.radius + self.radius + 10) ** 2:
            avoid_force = -to_obstacle
            if avoid_force.length_squared() > 0:
                avoid_force.scale_to_length(self.max_force * 2)
                self.acceleration += avoid_force

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), self.radius)

class Prey(Agent):
    energy_decay_rate = 0.01
    energy_gain_rate = 0.15
    reproduction_energy_cost = 75
    reproduction_interval = 400

    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = (46, 139, 87)  # Sea Green
        self.reproduction_timer = 0

    def update(self, prey_list, predator_list, width, height, obstacles, food_areas, hiding_spots, spatial_hash_prey, spatial_hash_predator, cell_size):
        self.energy -= self.energy_decay_rate
        if self.energy <= 0:
            prey_list.remove(self)
            return

        nearby_prey = self.get_nearby_agents(spatial_hash_prey, cell_size)
        nearby_predators = self.get_nearby_agents(spatial_hash_predator, cell_size)

        self.acceleration = (
            self.flock(nearby_prey) * 0.3 +
            self.evade(nearby_predators) * 2.5 +
            self.avoid_obstacles(obstacles) * 1.2 +
            self.seek_food(food_areas) * 0.5 +
            self.use_hiding_spots(hiding_spots, nearby_predators) * 0.7
        )

        self.acceleration = self.limit_force(self.acceleration)

        super().update(width, height)
        
        self.reproduction_timer += 1
        if self.reproduction_timer >= self.reproduction_interval and self.energy > self.reproduction_energy_cost:
            self.reproduce(prey_list)
            self.reproduction_timer = 0

    def get_nearby_agents(self, spatial_hash, cell_size):
        cell_x, cell_y = int(self.position.x // cell_size), int(self.position.y // cell_size)
        return [agent for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                for agent in spatial_hash.get((cell_x + dx, cell_y + dy), [])]

    def flock(self, nearby_prey):
        alignment = cohesion = separation = pygame.Vector2(0, 0)
        total = 0

        for other in nearby_prey:
            if other != self:
                offset = other.position - self.position
                distance_squared = offset.length_squared()
                
                if distance_squared > 0:  # Add this check
                    separation += offset.normalize() / math.sqrt(distance_squared)
                
                alignment += other.velocity
                cohesion += other.position
                total += 1

        if total > 0:
            alignment = (alignment / total).normalize() * self.max_speed - self.velocity
            cohesion = ((cohesion / total) - self.position).normalize() * self.max_speed - self.velocity
            separation = (separation / total).normalize() * self.max_speed - self.velocity

            return self.limit_force(alignment * 0.5 + cohesion * 0.3 + separation * 0.5)
        return pygame.Vector2(0, 0)

    def evade(self, nearby_predators):
        evade_force = pygame.Vector2(0, 0)
        for predator in nearby_predators:
            offset = self.position - predator.position
            distance_squared = offset.length_squared()
            if distance_squared < self.perception_radius_squared:
                if distance_squared > 0:
                    evade_force += offset.normalize() * self.max_speed
                else:
                    evade_force += pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * self.max_speed
        return self.limit_force(evade_force)

    def avoid_obstacles(self, obstacles):
        avoid_force = pygame.Vector2(0, 0)
        for obstacle in obstacles:
            offset = self.position - obstacle.position
            distance_squared = offset.length_squared()
            if distance_squared < (obstacle.radius + self.radius + 10) ** 2:
                avoid_force += offset.normalize() * self.max_speed
        return self.limit_force(avoid_force)

    def seek_food(self, food_areas):
        food_force = pygame.Vector2(0, 0)
        for food_area in food_areas:
            offset = food_area.position - self.position
            if offset.length_squared() < food_area.radius ** 2:
                self.energy = min(self.energy + self.energy_gain_rate, self.max_energy)
                food_force += self.seek(food_area.position)
        return self.limit_force(food_force)

    def use_hiding_spots(self, hiding_spots, nearby_predators):
        hiding_force = pygame.Vector2(0, 0)
        for hiding_spot in hiding_spots:
            for predator in nearby_predators:
                if (self.position - predator.position).length_squared() < self.perception_radius_squared:
                    offset = hiding_spot.position - self.position
                    if offset.length_squared() < hiding_spot.radius ** 2:
                        hiding_force += self.seek(hiding_spot.position)
                        self.velocity *= 0.8
        return self.limit_force(hiding_force)

    def reproduce(self, prey_list):
        if len(prey_list) < 150:  # Changed from 250 to 150
            self.energy -= self.reproduction_energy_cost
            new_prey = Prey(self.position.x, self.position.y)
            new_prey.energy = self.reproduction_energy_cost / 2
            prey_list.append(new_prey)

class Predator(Agent):
    energy_decay_rate = 0.015
    energy_gain_from_prey = 40
    reproduction_threshold = 6
    reproduction_energy_cost = 120

    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = (178, 34, 34)  # Firebrick
        self.prey_eaten = 0
        self.max_speed = 1.8

    def update(self, prey_list, predator_list, width, height, obstacles, food_areas, hiding_spots, spatial_hash_prey, spatial_hash_predator, cell_size):
        self.energy -= self.energy_decay_rate
        if self.energy <= 0:
            predator_list.remove(self)
            return

        nearby_prey = self.get_nearby_agents(spatial_hash_prey, cell_size)

        closest_prey = None
        closest_distance_squared = float('inf')

        for prey in nearby_prey:
            distance_squared = (prey.position - self.position).length_squared()
            if distance_squared < closest_distance_squared and distance_squared < self.perception_radius_squared:
                closest_prey = prey
                closest_distance_squared = distance_squared

        if closest_prey:
            self.acceleration = self.seek(closest_prey.position) * 0.8
        else:
            self.acceleration = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * (self.max_force * 0.5)

        for obstacle in obstacles:
            self.avoid_obstacle(obstacle)

        for hiding_spot in hiding_spots:
            offset = self.position - hiding_spot.position
            distance_squared = offset.length_squared()
            if distance_squared < (hiding_spot.radius * 1.5) ** 2:
                repel_force = offset.normalize() * self.max_force * 0.3
                self.acceleration += repel_force

        super().update(width, height)

        for prey in nearby_prey:
            if (self.position - prey.position).length_squared() < (self.radius + prey.radius) ** 2:
                if prey in prey_list:
                    prey_list.remove(prey)
                    self.prey_eaten += 1
                    self.energy = min(self.energy + self.energy_gain_from_prey, self.max_energy)
                
                    if self.prey_eaten >= self.reproduction_threshold and self.energy > self.reproduction_energy_cost * 1.2:
                        self.reproduce(predator_list)
                        self.prey_eaten = 0
                break

    def reproduce(self, predator_list):
        if len(predator_list) < 15:
            self.energy -= self.reproduction_energy_cost
            new_predator = Predator(self.position.x, self.position.y)
            new_predator.energy = self.reproduction_energy_cost / 2
            predator_list.append(new_predator)

    def get_nearby_cells(self, cell_size):
        x, y = int(self.position.x // cell_size), int(self.position.y // cell_size)
        return [
            (x + dx, y + dy)
            for dx in [-1, 0, 1]
            for dy in [-1, 0, 1]
        ]

    def get_nearby_agents(self, spatial_hash, cell_size):
        nearby_cells = self.get_nearby_cells(cell_size)
        nearby_agents = []
        for cell in nearby_cells:
            if cell in spatial_hash:
                nearby_agents.extend(spatial_hash[cell])
        return nearby_agents