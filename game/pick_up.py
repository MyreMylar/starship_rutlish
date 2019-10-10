import pygame
import random
from collision.collision_shapes import CollisionRect
from collision.collision_handling import CollisionNoHandler
from game.game_collision_types import CollisionType


class PickUpSpawner:
    def __init__(self, all_sprites, image_map, collision_grid):

        self.collision_grid = collision_grid
        self.all_sprites = all_sprites
        
        self.missile_image = image_map.subsurface((0, 448, 32, 32))
        self.life_image = image_map.subsurface((32, 448, 32, 32))
        self.shield_image = image_map.subsurface((0, 480, 32, 32))
        self.bomb_image = image_map.subsurface((32, 480, 32, 32))

        self.missile_upgrade_image = image_map.subsurface((64, 448, 32, 32))
        self.gun_upgrade_image = image_map.subsurface((64, 480, 32, 32))

    def try_spawn(self, base_chance, stage, spawn_position, spawn_heading):
        d100 = random.randint(1, 100)
        if d100 <= base_chance:
            d12 = random.randint(1, 12)
            if d12 < 8:
                d8 = random.randint(1, 8)
                if d8 == 8:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.life_image, "life",
                           self.collision_grid, self.all_sprites)
                elif 8 > d8 > 5:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.shield_image, "shield",
                           self.collision_grid, self.all_sprites)
                elif 5 > d8 > 3:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.missile_image, "missile",
                           self.collision_grid, self.all_sprites)
                else:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.bomb_image, "bomb",
                           self.collision_grid, self.all_sprites)
            elif d12 >= 8:
                d4 = random.randint(1, 4)
                if d4 == 4:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.missile_upgrade_image, "missile_upgrade",
                           self.collision_grid, self.all_sprites)
                else:
                    PickUp(stage, spawn_position, spawn_heading,
                           self.gun_upgrade_image, "gun_upgrade",
                           self.collision_grid, self.all_sprites)
            

class PickUp(pygame.sprite.Sprite):
    def __init__(self, stage, start_pos, start_heading, image, type_name, collision_grid, all_sprites):
        super().__init__(all_sprites)
        self.stage = stage

        self.position = [start_pos.x, start_pos.y]
        self.heading = start_heading
        self.type_name = type_name
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = self.position

        self.should_die = False

        self.collision_grid = collision_grid
        types_to_collide_with = [CollisionType.PLAYER]
        handler = CollisionNoHandler()
        handlers_by_type = {}
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_rect = CollisionRect(self.rect, 0, handlers_by_type,
                                            CollisionType.PICK_UP, types_to_collide_with)

        self.collision_grid.add_new_shape_to_grid(self.collision_rect)

    def update(self, time_delta):
        self.position[0] += self.heading[0] * time_delta
        self.position[1] += self.heading[1] * time_delta

        if self.position[0] < 0:
            self.position[0] = self.stage.width
                
        if self.position[0] > self.stage.width:
            self.position[0] = 0
        
        if self.position[1] < 0:
            self.position[1] = self.stage.height
            
        if self.position[1] > self.stage.height:
            self.position[1] = 0

        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.collision_rect.set_position(self.rect.center)

        if len(self.collision_rect.collided_shapes_this_frame) > 0:
            if self.type_name == "missile":
                self.stage.get_ship().add_missiles(3 + (self.stage.get_ship_stats().missiles_rank - 1))
            elif self.type_name == "shield":
                self.stage.get_ship().activate_shield(10.0)
            elif self.type_name == "life":
                self.stage.get_ship_stats().lives += 1
            elif self.type_name == "bomb":
                self.stage.get_ship().activate_bombs()
            elif self.type_name == "missile_upgrade":
                self.stage.get_ship_stats().upgrade_missiles()
                self.stage.get_ship().update_from_stats()
                self.stage.get_ship().add_missiles(3 + (self.stage.get_ship_stats().missiles_rank - 1))
            elif self.type_name == "gun_upgrade":
                self.stage.get_ship_stats().upgrade_guns()
                self.stage.get_ship().update_from_stats()

            self.die()

    def die(self):
        self.collision_grid.remove_shape_from_grid(self.collision_rect)
        self.kill()
