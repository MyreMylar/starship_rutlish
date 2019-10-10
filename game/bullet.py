import pygame
from collision.collision_shapes import CollisionRect
from collision.collision_handling import CollisionNoHandler


# Bullet class
class Bullet(pygame.sprite.Sprite):

    def __init__(self, position, heading, angle, shooter, ttl, velocity, stage, image_map, collision_grid, collide_type,
                 types_to_collide_with, rank, all_sprites):

        super().__init__(all_sprites)
        self.position = position
        self.heading = heading
        self.angle = angle
        self.shooter = shooter
        self.stage = stage
        self.ttl = ttl
        self.velocity = velocity
        self.rank = rank

        self.bullet_endurance = 1

        self.regular_bullet_image = image_map.subsurface((0, 576, 3, 4))
        self.long_bullet_image = image_map.subsurface((10, 576, 3, 6))
        self.copper_bullet_image = image_map.subsurface((13, 576, 3, 6))
        self.laser_bullet_image = image_map.subsurface((16, 576, 4, 6))
        self.plasma_bullet_image = image_map.subsurface((20, 576, 6, 8))

        if self.rank == 1:
            self.current_bullet_image = self.regular_bullet_image
        elif self.rank == 2:
            self.current_bullet_image = self.long_bullet_image
        elif self.rank == 3:
            self.current_bullet_image = self.copper_bullet_image
        elif self.rank == 4:
            self.current_bullet_image = self.laser_bullet_image
            self.bullet_endurance = 2
        elif self.rank == 5:
            self.current_bullet_image = self.plasma_bullet_image
            self.bullet_endurance = 4

        self.sprite_rot_centre_offset = [0.0, 0.0]
        self.image = self.current_bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (self.position.x, self.position.y)

        self.collision_grid = collision_grid
        handler = CollisionNoHandler()
        handlers_by_type = {}
        types_to_collide_with = types_to_collide_with
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_rect = CollisionRect(self.rect, self.angle, handlers_by_type,
                                            collide_type, types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_rect)

    def die(self):
        self.shooter.bullets.remove(self)
        self.collision_grid.remove_shape_from_grid(self.collision_rect)
        self.kill()

    def update(self, time_delta):
        self.ttl -= time_delta
        if len(self.collision_rect.collided_shapes_this_frame) > 0:
            self.bullet_endurance -= 1
        if self.ttl <= 0 or self.bullet_endurance == 0:
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

        self.image = pygame.transform.rotate(self.current_bullet_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.math.Vector2(0.0, self.sprite_rot_centre_offset[1]).rotate(self.angle) + self.position

        self.collision_rect.set_position(self.rect.center)
        self.collision_rect.set_rotation(self.angle)
