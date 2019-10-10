import math
import pygame

from collision.collision_shapes import CollisionRect
from collision.collision_handling import CollisionNoHandler
from game.game_collision_types import CollisionType


# Missile class
class Missile(pygame.sprite.Sprite):

    def __init__(self, stage, position, heading, shooter, ttl, velocity, angle, target, rock_list, image_map,
                 collision_grid, all_sprites):

        super().__init__(all_sprites)
        self.position = pygame.math.Vector2(position)
        self.heading = heading
        self.angle = angle
        self.target_angle = angle
        self.turn_speed = 600.0

        self.stage = stage
        self.shooter = shooter
        self.ttl = ttl
        self.velocity = velocity
        self.target = target
        self.is_homing_time = False
        self.homing_time_counter = 0
        self.homing_time_limit = 10
        self.missile_velocity = 10.0
        self.rock_list = rock_list

        self.missile_image = image_map.subsurface((4, 576, 7, 19))

        self.sprite_rot_centre_offset = [0.0, 0.0]
        self.image = self.missile_image
        self.rect = self.missile_image.get_rect()
        self.rect.center = (self.position.x, self.position.y)

        self.collision_grid = collision_grid
        types_to_collide_with = [CollisionType.ROCK, CollisionType.AI_SHIPS]
        handler = CollisionNoHandler()
        handlers_by_type = {}
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_rect = CollisionRect(self.rect, self.angle, handlers_by_type,
                                            CollisionType.MISSILES, types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_rect)

    def update(self, time_delta):
        self.ttl -= time_delta

        if not self.is_homing_time:
            self.homing_time_counter += 1
            if self.homing_time_counter >= self.homing_time_limit:
                self.is_homing_time = True

        if self.target is not None and not self.target.dead and self.is_homing_time:

            final_target_x = self.target.position.x
            final_target_y = self.target.position.y
            # check normal screen x distance
            x_normal_dist = self.position.x - self.target.position.x
            x_normal_dist_squared = x_normal_dist * x_normal_dist

            # check distance when overlapping the screen
            x_dist_from_far_side = self.position.x - float(self.stage.width)
            x_overlap_dist_squared1 = (self.target.position.x ** 2) + (x_dist_from_far_side ** 2)

            x_dist_from_far_side_to_target = float(self.stage.width) - self.target.position.x
            x_overlap_dist_squared2 = (self.position.x ** 2) + (x_dist_from_far_side_to_target ** 2)

            # compare the three potential paths to target and pick shortest
            x_dist_final = x_normal_dist_squared
            if x_dist_final > x_overlap_dist_squared1:
                x_dist_final = x_overlap_dist_squared1
                final_target_x = float(self.stage.width)
            if x_dist_final > x_overlap_dist_squared2:
                # x_dist_final = x_overlap_dist_squared2
                final_target_x = 0.0

            # check normal screen y distance
            y_normal_dist = self.position.y - self.target.position.y
            y_normal_dist_squared = y_normal_dist * y_normal_dist

            # check distance when overlapping the screen
            y_dist_from_far_side = self.position.y - float(self.stage.height)
            y_overlap_dist_squared1 = (self.target.position.y ** 2) + (y_dist_from_far_side ** 2)

            y_dist_from_far_side_to_target = float(self.stage.height) - self.target.position.y
            y_overlap_dist_squared2 = (self.position.y ** 2) + (y_dist_from_far_side_to_target ** 2)

            # compare the three potential paths to target and pick shortest
            y_dist_final = y_normal_dist_squared
            if y_dist_final > y_overlap_dist_squared1:
                y_dist_final = y_overlap_dist_squared1
                final_target_y = float(self.stage.height)
            if y_dist_final > y_overlap_dist_squared2:
                # y_dist_final = y_overlap_dist_squared2
                final_target_y = 0.0

            y_result = final_target_y - self.position.y
            x_result = final_target_x - self.position.x
            result = math.degrees(math.atan2(-x_result, -y_result))
            self.target_angle = result

            if self.target_angle < 0:
                self.target_angle = self.target_angle + 360.0
            if self.target_angle > 360:
                self.target_angle = self.target_angle - 360.0

            if self.target_angle > 360.0:
                print("large target:" + str(self.target_angle))

            if self.angle != self.target_angle:
                cw_rotational_distance = abs(self.angle - self.target_angle)
                if cw_rotational_distance < 180.0:
                    # we want the missiles to turn slowly when they are close to aiming directly at the target
                    # so we use a cubic series that maintains the speed close to 1.0 until we are near
                    rot_fac = (max(0.001, min(180.0, (180.0 - cw_rotational_distance)))/180.0) ** 3
                    rotational_distance_factor = 1.0 - rot_fac
                    if self.target_angle > self.angle:
                        self.angle += self.turn_speed * time_delta * rotational_distance_factor
                    else:
                        self.angle -= self.turn_speed * time_delta * rotational_distance_factor
                else:
                    cw_rotational_distance = 180 - (cw_rotational_distance - 180)
                    rot_fac = (max(0.001, min(180.0, (180.0 - cw_rotational_distance)))/180.0) ** 3
                    rotational_distance_factor = 1.0 - rot_fac
                    if self.target_angle > self.angle:
                        self.angle -= self.turn_speed * time_delta * rotational_distance_factor
                    else:
                        self.angle += self.turn_speed * time_delta * rotational_distance_factor

                if self.angle < 0:
                    self.angle = self.angle + 360.0

                if self.angle > 360:
                    self.angle = self.angle - 360.0

            vx = self.missile_velocity * math.sin(math.radians(self.angle)) * -1
            vy = self.missile_velocity * math.cos(math.radians(self.angle)) * -1
            self.heading = pygame.math.Vector2(vx, vy)

        if self.target is None or self.target.dead and self.is_homing_time:
            # find new target
            shortest_distance = 100000000.0
            for rock in self.rock_list:
                distance = self.calculate_distance(self, rock)
                if distance < shortest_distance:
                    shortest_distance = distance
                    self.target = rock

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

        self.image = pygame.transform.rotate(self.missile_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.math.Vector2(0.0, self.sprite_rot_centre_offset[1]).rotate(self.angle) + self.position

        self.collision_rect.set_position(self.rect.center)
        self.collision_rect.set_rotation(self.angle)

        if self.ttl <= 0 or len(self.collision_rect.collided_shapes_this_frame) > 0:
            self.die()

    def die(self):
        self.shooter.missiles.remove(self)
        self.collision_grid.remove_shape_from_grid(self.collision_rect)
        self.kill()

    # calculates the distance between two objects
    def calculate_distance(self, start_object, finish_object):
        # check normal screen x distance
        x_normal_dist = start_object.position.x - finish_object.position.x
        x_normal_dist_squared = x_normal_dist * x_normal_dist

        # check distance when overlapping the screen
        x_dist_from_far_side = start_object.position.x - float(self.stage.width)
        x_overlap_dist_squared1 = (finish_object.position.x ** 2) + (x_dist_from_far_side ** 2)

        x_dist_from_far_side_to_target = float(self.stage.width) - finish_object.position.x
        x_overlap_dist_squared2 = (start_object.position.x ** 2) + (x_dist_from_far_side_to_target ** 2)

        # compare the three potential paths to target and pick shortest
        x_dist_final = x_normal_dist_squared
        if x_dist_final > x_overlap_dist_squared1:
            x_dist_final = x_overlap_dist_squared1
        if x_dist_final > x_overlap_dist_squared2:
            x_dist_final = x_overlap_dist_squared2

        # check normal screen y distance
        y_normal_dist = start_object.position.y - finish_object.position.y
        y_normal_dist_squared = y_normal_dist ** 2

        # check distance when overlapping the screen
        y_dist_from_far_side = start_object.position.y - float(self.stage.height)
        y_overlap_dist_squared1 = (finish_object.position.y ** 2) + (y_dist_from_far_side ** 2)

        y_dist_from_far_side_to_target = float(self.stage.height) - finish_object.position.y
        y_overlap_dist_squared2 = (start_object.position.y ** 2) + (y_dist_from_far_side_to_target ** 2)

        # compare the three potential paths to target and pick shortest
        y_dist_final = y_normal_dist_squared
        if y_dist_final > y_overlap_dist_squared1:
            y_dist_final = y_overlap_dist_squared1
        if y_dist_final > y_overlap_dist_squared2:
            y_dist_final = y_overlap_dist_squared2

        distance = math.sqrt(x_dist_final + y_dist_final)

        return distance
