import pygame
from collision.collision_shapes import CollisionCircle, CollisionRect
from collision.collision_handling import CollisionNoHandler
from game.game_collision_types import CollisionType


class BombExplosion(pygame.sprite.Sprite):

    def __init__(self, position, collision_grid, all_sprites):

        super().__init__(all_sprites)
        self.image = pygame.Surface((256, 256)).convert_alpha()
        self.image.fill(pygame.Color(0,0,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = position
        pygame.draw.circle(self.image, pygame.Color('#FFFFFF'), (128, 128), 128, 2)
        self.collision_grid = collision_grid
        handler = CollisionNoHandler()
        handlers_by_type = {}
        types_to_collide_with = [CollisionType.ROCK, CollisionType.AI_SHIPS]
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_shape = CollisionCircle(self.rect.centerx, self.rect.centery,
                                               128, handlers_by_type,
                                               CollisionType.BOMB_EXPLOSION,
                                               types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_shape)

        self.life_time = 0.5

    def die(self):
        self.collision_grid.remove_shape_from_grid(self.collision_shape)
        self.kill()

    def update(self, time_delta):
        self.life_time -= time_delta
        if self.life_time <= 0.0:
            self.die()


# Bomb class
class Bomb(pygame.sprite.Sprite):

    def __init__(self, position, heading, image, stage, collision_grid, all_sprites):
        super().__init__(all_sprites)
        self.position = position
        self.heading = heading
        self.stage = stage
        self.life_time = 0.75
        self.all_sprites = all_sprites

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (self.position.x, self.position.y)

        self.collision_grid = collision_grid
        handler = CollisionNoHandler()
        handlers_by_type = {}
        types_to_collide_with = [CollisionType.ROCK, CollisionType.AI_SHIPS]
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_rect = CollisionRect(self.rect, 0, handlers_by_type,
                                            CollisionType.BOMB, types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_rect)

    def die(self):
        BombExplosion(self.position, self.collision_grid, self.all_sprites)
        self.collision_grid.remove_shape_from_grid(self.collision_rect)
        self.kill()

    def update(self, time_delta):
        self.life_time -= time_delta
        if len(self.collision_rect.collided_shapes_this_frame) > 0 or self.life_time <= 0.0:
            self.die()

        self.position.x = self.position.x + self.heading.x
        self.position.y = self.position.y + self.heading.y

        if self.position.x < 0:
            self.position.x = self.stage.width

        if self.position.x > self.stage.width:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = self.stage.height

        if self.position.y > self.stage.height:
            self.position.y = 0

        self.rect.center = (self.position.x, self.position.y)
        self.collision_rect.set_position(self.rect.center)

