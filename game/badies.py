import random
import math
import pygame

from game.sound_manager import *
from game.bullet import Bullet
from collision.collision_handling import CollisionNoHandler
from collision.collision_shapes import CollisionCircle, CollisionRect
from game.game_collision_types import CollisionType


# Four different shape of rock each of which can be small, medium or large.
# Smaller rocks are faster.
class Rock(pygame.sprite.Sprite):

    # indexes into the tuples below
    large_rock_type = 0
    medium_rock_type = 1
    small_rock_type = 2
    
    velocities = (90.0, 240.0, 360.0)    
    scales = (2.5, 1.5, 0.6)

    # tracks the last rock shape to be generated
    rockShape = 1    
    
    # Create the rock polygon to the given scale
    def __init__(self, stage, position, rock_type, rock_sprite_table, all_sprites, collision_grid):
        super().__init__(all_sprites)

        self.rock_sprite_table = rock_sprite_table
        self.stage = stage
        scale = Rock.scales[rock_type]
        self.speed = Rock.velocities[rock_type]
        self.spin_speed = 60.0
        self.position = pygame.math.Vector2(position)
        self.heading = pygame.math.Vector2(random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0))
        self.angle = 0
        
        # Ensure that the rocks don't just sit there or move along regular lines
        if self.heading.x == 0:
            self.heading.x = 0.1
        
        if self.heading.y == 0:
            self.heading.y = 0.1
                        
        self.rock_type = rock_type
        rock_x_index = random.randint(0, 4)
        rock_y_index = random.randint(0, 5)

        self.original_image = self.rock_sprite_table[rock_y_index][rock_x_index].copy()
        self.original_image = pygame.transform.scale(self.original_image, (int(scale*32), int(scale*32)))

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.sprite_rot_centre_offset = pygame.math.Vector2(0.0, 0.0)
        self.rect.center = (self.position.x, self.position.y)

        self.collision_grid = collision_grid
        handler = CollisionNoHandler()
        types_to_collide_with = [CollisionType.PLAYER, CollisionType.BULLETS, CollisionType.MISSILES,
                                 CollisionType.BOMB, CollisionType.BOMB_EXPLOSION]
        self.collision_circle = CollisionCircle(self.position.x, self.position.y, scale*16,
                                                {CollisionType.PLAYER: handler,
                                                 CollisionType.BULLETS: handler,
                                                 CollisionType.MISSILES: handler,
                                                 CollisionType.BOMB: handler,
                                                 CollisionType.BOMB_EXPLOSION: handler},
                                                CollisionType.ROCK, types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_circle)

        self.dead = False
    
    # Create different rock type point lists
    def die(self):
        self.dead = True
        self.collision_grid.remove_shape_from_grid(self.collision_circle)
        self.kill()

    # Spin the rock when it moves
    def update(self, time_delta):

        self.position.x = self.position.x + (self.heading.x * time_delta * self.speed)
        self.position.y = self.position.y + (self.heading.y * time_delta * self.speed)

        if self.position.x < 0:
            self.position.x = self.stage.width
                
        if self.position.x > self.stage.width:
            self.position.x = 0
        
        if self.position.y < 0:
            self.position.y = self.stage.height
            
        if self.position.y > self.stage.height:
            self.position.y = 0
            
        # Original Asteroid didn't have spinning rocks but they look nicer
        self.angle += self.spin_speed * time_delta

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.position + self.sprite_rot_centre_offset.rotate(self.angle)

        self.collision_circle.set_position(self.rect.center)

    def try_pick_up_spawn(self, pickup_spawner):
        if pickup_spawner is not None:
            pickup_spawner.try_spawn(15, self.stage, self.position, -self.heading * self.speed * 0.5)
        

class Debris(pygame.sprite.Sprite):
    initial_life_time = 5.0

    def __init__(self, position, coloured_surface, *groups):
        super().__init__(*groups)
        self.position = pygame.math.Vector2(position)
        self.heading = pygame.math.Vector2(random.uniform(-150, 150), random.uniform(-150, 150))
        self.life_time = Debris.initial_life_time
        self.image = coloured_surface
        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.alpha = 255

    def update(self, time_delta):
        self.position += self.heading * time_delta
        self.life_time -= time_delta
        self.rect.center = self.position
        if self.life_time <= 0.0:
            self.kill()
        else:
            self.alpha = 255 * (self.life_time / Debris.initial_life_time)
            self.image.set_alpha(self.alpha)
        

# Flying saucer, shoots at player
class Saucer(pygame.sprite.Sprite):
    
    # indexes into the tuples below
    large_saucer_type = 0
    small_saucer_type = 1

    velocities = (170, 300)
    scales = (1.5, 1.0)
    scores = (500, 1000)

    maxBullets = 1
    bullet_ttl = [60, 90]
    bullet_velocity = 5
    
    def __init__(self, stage, saucer_type, ship, sound_manager, image_map, collision_grid, all_sprites):

        super().__init__(all_sprites)
        self.all_sprites = all_sprites
        self.stage = stage
        self.sound_manager = sound_manager
        self.bullets = []
        self.image_map = image_map
        self.collision_grid = collision_grid
        self.position = pygame.math.Vector2(0.0, random.randrange(0, stage.height))
        self.heading = pygame.math.Vector2(self.velocities[saucer_type], 0.0)
        self.saucer_type = saucer_type
        self.ship = ship
        self.score_value = self.scores[saucer_type]
        self.sound_manager.stop_sound("s_saucer")
        self.sound_manager.stop_sound("l_saucer")
        if saucer_type == self.large_saucer_type:
            self.sound_manager.play_sound_continuous("l_saucer")
        else:            
            self.sound_manager.play_sound_continuous("s_saucer")
        self.laps = 0
        self.last_x = 0

        self.ship_image = image_map.subsurface((128, 384, 53, 27))

        self.sprite_rot_centre_offset = [0.0, 0.0]

        self.image = self.ship_image
        self.rect = self.ship_image.get_rect()
        self.rect.center = (self.position.x, self.position.y)

        self.collision_grid = collision_grid
        types_to_collide_with = [CollisionType.BULLETS,
                                 CollisionType.MISSILES,
                                 CollisionType.BOMB,
                                 CollisionType.BOMB_EXPLOSION,
                                 CollisionType.ROCK]
        handler = CollisionNoHandler()
        handlers_by_type = {}
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_shape = CollisionRect(self.rect, 0, handlers_by_type,
                                             CollisionType.AI_SHIPS, types_to_collide_with)

        self.collision_grid.add_new_shape_to_grid(self.collision_shape)

    def update(self, time_delta):

        if (self.position.x > self.stage.width * 0.33) and (self.position.x < self.stage.width * 0.66):
            self.heading.y = self.heading.x
        else:
            self.heading.y = 0

        if self.ship is not None:
            dx = self.ship.position.x - self.position.x
            dy = self.ship.position.y - self.position.y
            mag = math.sqrt(dx**2 + dy**2)
            heading = pygame.math.Vector2(self.bullet_velocity * (dx / mag), self.bullet_velocity * (dy / mag))

            angle = math.atan2(heading.x, heading.y)
            angle = angle * 180 / math.pi

            self.fire_bullet(heading, self.bullet_velocity, angle)

        self.position.x += self.heading.x * time_delta
        self.position.y += self.heading.y * time_delta

        if self.position.x < 0:
            self.position.x = self.stage.width

        if self.position.x > self.stage.width:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = self.stage.height

        if self.position.y > self.stage.height:
            self.position.y = 0

        # have we lapped?        
        if self.last_x > self.position.x:
            self.last_x = 0
            self.laps += 1
        else:
            self.last_x = self.position.x

        self.rect.center = (self.position.x, self.position.y)
        self.collision_shape.set_position(self.rect.center)
                
    # Set the bullet velocity and create the bullet
    def fire_bullet(self, heading, velocity, angle):
        if len(self.bullets) < self.maxBullets:
            position = pygame.math.Vector2(self.position.x, self.position.y)
            new_bullet = Bullet(position, heading, angle, self, 2.0,
                                velocity, self.stage, self.image_map, self.collision_grid,
                                CollisionType.AI_BULLETS, [CollisionType.ROCK, CollisionType.PLAYER,
                                                           CollisionType.MISSILES], 1, self.all_sprites)
            self.bullets.append(new_bullet)
            return True

    def die(self):
        self.collision_grid.remove_shape_from_grid(self.collision_shape)
        self.kill()

    def try_pick_up_spawn(self, pickup_spawner):
        pickup_spawner.try_spawn(75, self.stage, self.position, pygame.math.Vector2(-self.heading.x, -self.heading.y))
        pickup_spawner.try_spawn(50, self.stage, self.position, pygame.math.Vector2(self.heading.x, -self.heading.y))
        pickup_spawner.try_spawn(20, self.stage, self.position, pygame.math.Vector2(-self.heading.y, self.heading.x))
