import math
from game.input_manager import *
from game.badies import *
from game.sound_manager import *
from game.bullet import Bullet
from game.missile import Missile
from game.bomb import Bomb
from collision.collision_shapes import CollisionRect
from game.game_collision_types import CollisionType


class ShieldSprite(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.rect = None
        self.image = None


# Ship class
class Ship(pygame.sprite.Sprite):
            
    # Class attributes
    deceleration = -0.005
    turn_angle = 6
    bullet_velocity = 15.0
    missile_velocity = 10.0

    bullet_ttl = 35
    missile_range = 90
    
    def __init__(self, stage, input_manager, sound_manager, stats, image_map, collision_grid,
                 debris_colour, top_speed, acceleration, all_sprites):
        self.all_sprites = all_sprites
        super().__init__(all_sprites)
        self.image_map = image_map
        self.collision_grid = collision_grid
        self.bullets = []
        self.missiles = []

        self.debris_surface = pygame.Surface((1, 1))
        self.debris_surface.fill(debris_colour)

        self.acceleration = acceleration
        self.stats = stats
        self.max_velocity = top_speed
        self.input_manager = input_manager
        self.sound_manager = sound_manager
        self.position = pygame.math.Vector2(stage.width/2, stage.height/2)
        self.heading = pygame.math.Vector2(0.0, 0.0)
        self.angle = 0       
        self.ship_debris_list = []
        self.visible = True   
        self.in_hyper_space = False
        self.point_list = [(0, -10), (6, 10), (3, 7), (-3, 7), (-6, 10)]
        self.transformed_point_list = [(0, -10), (6, 10), (3, 7), (-3, 7), (-6, 10)]

        self.base_max_bullets = 4
        self.speed = 60.0
        self.name = "ship"
        self.gun_repeat_time = 0.3
        self.gun_repeat_timer = 0.0
        self.can_fire_gun = True

        self.stage = stage

        self.missile_target = None
        self.missile_repeat_time = 0.5
        self.missile_repeat_timer = 0.0
        self.can_fire_missile = True

        self.can_hyper_space = True

        self.accelerating = False

        self.missile_count = 5
        self.lives = 3

        self.original_image = image_map.subsurface((0, 384, 32, 54))
        self.sprite_rot_centre_offset = [0.0, 0.0]

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (self.position.x, self.position.y)

        self.shield_sprite_image = image_map.subsurface((64, 384, 64, 64))

        types_to_collide_with = [CollisionType.ROCK, CollisionType.AI_SHIPS,
                                 CollisionType.AI_BULLETS, CollisionType.PICK_UP]

        handler = CollisionNoHandler()
        handlers_by_type = {}
        for type in types_to_collide_with:
            handlers_by_type[type] = handler
        self.collision_shape = CollisionRect(self.rect, self.angle, handlers_by_type,
                                             CollisionType.PLAYER, types_to_collide_with)

        self.collision_grid.add_new_shape_to_grid(self.collision_shape)

        self.exploding = False

        self.is_shield_active = True
        self.shield_activity_timer = 0.0
        self.shield_time = 0.0
        self.shield_flicker_dur = 1.5
        self.shield_flicker_time_per_flick = 0.1
        self.shield_flicker_acc = 0.0
        self.shield_flickering = False
        self.shield_flicker_state = False

        self.shield_sprite = None
        self.activate_shield(3.5)

        self.time_delta = 0.1
        self.rock_list = None

        self.left_rot_acc = 0.0
        self.right_rot_acc = 0.0

        self.rot_acc_speed = 120.0
        self.top_rot_speed = 60.0
        self.hyper_space_ttl = 100

        self.bomb_mode = False
        self.bombs_left = 0

    def update_from_stats(self):
        self.gun_repeat_time = 0.6 - (self.stats.guns_rank * 0.115)
        self.missile_repeat_time = 0.8 - (self.stats.missiles_rank * 0.2)

    def activate_bombs(self):
        self.bomb_mode = True
        self.bombs_left += 3

    def deactivate_bombs(self):
        self.bomb_mode = False

    def activate_shield(self, time):
        self.is_shield_active = True
        self.shield_flickering = False
        self.shield_activity_timer = 0.0
        self.shield_time = time

        if self.shield_sprite is None:
            self.shield_sprite = ShieldSprite(self.all_sprites)
            self.shield_sprite.image = self.shield_sprite_image
            self.shield_sprite.rect = self.shield_sprite.image.get_rect()
            self.shield_sprite.rect.center = (self.position.x, self.position.y)

    def flicker_shield(self):
        if self.shield_flicker_state:
            self.shield_flicker_state = False
            if self.shield_sprite is not None:
                self.shield_sprite.kill()
                self.shield_sprite = None
        else:
            self.shield_flicker_state = True
            if self.shield_sprite is None:
                self.shield_sprite = ShieldSprite(self.all_sprites)
                self.shield_sprite.image = self.shield_sprite_image
                self.shield_sprite.rect = self.shield_sprite.image.get_rect()
                self.shield_sprite.rect.center = (self.position.x, self.position.y)

    def deactivate_shield(self):
        if self.shield_sprite is not None:
            self.shield_sprite.kill()
            self.shield_sprite = None

    def update_rock_list(self, rock_list):
        self.rock_list = rock_list

    def rotate_left(self, time_delta):
        self.left_rot_acc += time_delta * self.rot_acc_speed
        if self.left_rot_acc > self.top_rot_speed:
            self.left_rot_acc = self.top_rot_speed
        self.angle += (self.turn_angle * self.left_rot_acc * time_delta)
        
    def rotate_right(self, time_delta):
        self.right_rot_acc += time_delta * self.rot_acc_speed
        if self.right_rot_acc > self.top_rot_speed:
            self.right_rot_acc = self.top_rot_speed
        self.angle -= (self.turn_angle * self.right_rot_acc * time_delta)

    def rotate_analog(self, speed):
        self.angle -= (self.turn_angle * speed)
        
    def increase_thrust(self):
        if not self.accelerating:
            self.accelerating = True
            self.sound_manager.play_sound_continuous("thrust")
        if math.hypot(self.heading.x, self.heading.y) > self.max_velocity:
            return
        
        dx = self.acceleration * math.sin(math.radians(self.angle)) * -1
        dy = self.acceleration * math.cos(math.radians(self.angle)) * -1
        self.change_velocity(dx, dy)

    def increase_thrust_analog(self, thrust_value):
        if not self.accelerating:
            self.accelerating = True
            self.sound_manager.play_sound_continuous("thrust")
        if math.hypot(self.heading.x, self.heading.y) > self.max_velocity:
            return
        
        dx = self.acceleration * math.sin(math.radians(self.angle)) * -1 * thrust_value
        dy = self.acceleration * math.cos(math.radians(self.angle)) * -1 * thrust_value
        self.change_velocity(dx, dy)
    
    def decrease_thrust(self):
        if self.heading.x == 0 and self.heading.y == 0:
            return
        
        dx = self.heading.x * self.deceleration
        dy = self.heading.y * self.deceleration
        self.change_velocity(dx, dy)
    
    def change_velocity(self, dx, dy):
        self.heading.x += dx
        self.heading.y += dy
        
    def update(self, time_delta):
        self.update_timers(time_delta)
        self.time_delta = time_delta
        self.position.x = self.position.x + (self.heading.x * self.speed * time_delta)
        self.position.y = self.position.y + (self.heading.y * self.speed * time_delta)

        # when we reach the edges of the screen shift our sprite to be on the opposite side of the screen
        if self.position.x < 0:
            self.position.x = self.stage.width

        if self.position.x > self.stage.width:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = self.stage.height

        if self.position.y > self.stage.height:
            self.position.y = 0

        self.decrease_thrust()
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.rot_point([self.position.x,
                                           self.position.y + self.sprite_rot_centre_offset[1]],
                                          (self.position.x, self.position.y), -self.angle)

        if self.shield_sprite is not None:
            self.shield_sprite.rect.center = self.rect.center

        self.collision_shape.set_position(self.rect.center)
        self.collision_shape.set_rotation(self.angle)

        if self.bombs_left == 0:
            self.deactivate_bombs()

    def die(self):
        self.collision_grid.remove_shape_from_grid(self.collision_shape)
        self.kill()
        if self.shield_sprite is not None:
            self.shield_sprite.kill()
        self.exploding = True
        explosion_pos = (self.position.x, self.position.y)
        for _ in range(0, 60):
            position = pygame.math.Vector2(explosion_pos[0], explosion_pos[1])
            Debris(position, self.debris_surface, self.all_sprites)

    # Set the bullet velocity and create the bullet
    def fire_bullet(self):
        if not self.in_hyper_space:
            vx = self.bullet_velocity * math.sin(math.radians(self.angle)) * -1
            vy = self.bullet_velocity * math.cos(math.radians(self.angle)) * -1
            heading = pygame.math.Vector2(vx, vy)
            self.fire_bullet2(heading, 0.4 + (0.1 * self.stats.guns_rank), self.bullet_velocity, self.angle)
            self.sound_manager.play_sound("fire")
    
    # Set the missile velocity and create the missile
    def fire_missile(self):
        if self.bomb_mode and self.bombs_left > 0:
            vx = self.missile_velocity * math.sin(math.radians(self.angle)) * -1
            vy = self.missile_velocity * math.cos(math.radians(self.angle)) * -1
            heading = pygame.math.Vector2(vx, vy)
            position = pygame.math.Vector2(self.position.x, self.position.y)
            new_missile = Bomb(position, heading,
                               self.image_map.subsurface((26, 576, 14, 20)),
                               self.stage,
                               self.collision_grid, self.all_sprites)
            self.bombs_left -= 1
        else:
            if not self.in_hyper_space:
                vx = self.missile_velocity * math.sin(math.radians(self.angle)) * -1
                vy = self.missile_velocity * math.cos(math.radians(self.angle)) * -1
                heading = pygame.math.Vector2(vx, vy)
                self.fire_missile2(heading, self.missile_range, self.bullet_velocity,
                                   self.angle, self.missile_target, self.rock_list)
                self.sound_manager.play_sound("missile")
                self.missile_count -= 1
    
    def set_missile_target(self, target):
        self.missile_target = target
            
    def enter_hyper_space(self):
        if not self.in_hyper_space:
            self.in_hyper_space = True
            self.hyper_space_ttl = 100

    def process_input_events(self):
        key = pygame.key.get_pressed()

        ship_accelerating = False
     
        # keyboard controls
        if key[K_LEFT]:
            self.rotate_left(self.time_delta)
        else:
            self.left_rot_acc = 0.0

        if key[K_RIGHT]:
            self.rotate_right(self.time_delta)
        else:
            self.right_rot_acc = 0.0
        
        if key[K_UP]:
            self.increase_thrust()
            ship_accelerating = True

        if key[K_SPACE] and self.can_fire_gun is True:
            self.fire_bullet()
            self.can_fire_gun = False
            self.gun_repeat_timer = 0.0

        if (key[K_RSHIFT] or key[K_LSHIFT]) and self.can_fire_missile is True and (self.missile_count > 0
                                                                                   or self.bombs_left > 0):
            self.fire_missile()
            self.can_fire_missile = False
            self.missile_repeat_timer = 0.0

        # joystick controls
        if self.input_manager.joystick is not None:

            self.rotate_analog(self.input_manager.get_mapped_axis_value('right_stick_x'))

            thrust_value = -self.input_manager.get_mapped_axis_value('right_stick_y')
            if thrust_value > 0.0001:
                self.increase_thrust_analog(thrust_value)
                ship_accelerating = True

            gun_trigger_value = self.input_manager.get_mapped_axis_value('right_trigger')
            if(gun_trigger_value > 0.5) and self.can_fire_gun is True:
                self.fire_bullet()
                self.can_fire_gun = False
                self.gun_repeat_timer = 0.0
            r_b = self.input_manager.controller_buttons[self.input_manager.button_right_bumper['key']]['value'] != 0
            l_b = self.input_manager.controller_buttons[self.input_manager.button_left_bumper['key']]['value'] != 0
            bumper_press = r_b or l_b
            if bumper_press and self.can_fire_missile is True and self.missile_count > 0:
                self.fire_missile()
                self.can_fire_missile = False
                self.missile_repeat_timer = 0.0

        if not ship_accelerating:
            self.accelerating = False  
            self.sound_manager.stop_sound("thrust")

    def update_timers(self, time_delta):
        # gun auto fire
        seconds_since_last_frame = time_delta
        if self.can_fire_gun is False:
            self.gun_repeat_timer += seconds_since_last_frame
            if self.gun_repeat_timer > self.gun_repeat_time:
                self.can_fire_gun = True

        if self.can_fire_missile is False:
            self.missile_repeat_timer += seconds_since_last_frame
            if self.missile_repeat_timer > self.missile_repeat_time:
                self.can_fire_missile = True

        if self.is_shield_active is True:
            self.shield_activity_timer += seconds_since_last_frame
            if self.shield_activity_timer > self.shield_time - self.shield_flicker_dur:
                self.shield_flickering = True
            if self.shield_activity_timer > self.shield_time:
                self.shield_flickering = False
                self.is_shield_active = False
                self.deactivate_shield()

        if self.shield_flickering is True:
            self.shield_flicker_acc += seconds_since_last_frame
            if self.shield_flicker_acc > self.shield_flicker_time_per_flick:
                self.shield_flicker_acc = 0.0
                self.flicker_shield()

    @staticmethod
    def rot_point(point, axis, ang):
        """ Orbit. calculates the new loc for a point that rotates a given num of degrees around an axis point,
        +clockwise, -anticlockwise -> tuple x,y
        """
        ang -= 90
        x, y = point[0] - axis[0], point[1] - axis[1]
        radius = math.sqrt(x*x + y*y)  # get the distance between points

        r_ang = math.radians(ang)  # convert ang to radians.

        h = axis[0] + (radius * math.cos(r_ang))
        v = axis[1] + (radius * math.sin(r_ang))

        return [h, v]

    def add_missiles(self, num):
        self.missile_count += num

    def fire_bullet2(self, heading, ttl, velocity, angle):
        if len(self.bullets) < (self.base_max_bullets + self.stats.guns_rank * 2):
            position = pygame.math.Vector2(self.position.x, self.position.y)

            if self.stats.guns_rank == 1:
                new_bullet = Bullet(position, heading, angle, self, ttl,
                                    velocity, self.stage, self.image_map, self.collision_grid,
                                    CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                    self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet)
            elif self.stats.guns_rank == 2:
                heading_len = math.sqrt(heading.x ** 2 + heading.y ** 2)
                normal_heading = [heading.x/heading_len, heading.y/heading_len]
                left_gun_pos = pygame.math.Vector2(self.position.x + (normal_heading[1]*15) - (normal_heading[0] * 6),
                                        self.position.y - (normal_heading[0]*15) - (normal_heading[1] * 6))
                right_gun_pos = pygame.math.Vector2(self.position.x - (normal_heading[1]*15) - (normal_heading[0] * 6),
                                         self.position.y + (normal_heading[0]*15) - (normal_heading[1] * 6))
                new_bullet_1 = Bullet(left_gun_pos, heading, angle, self, ttl,
                                      velocity, self.stage, self.image_map, self.collision_grid,
                                      CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                      self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet_1)
                new_bullet_2 = Bullet(right_gun_pos, heading, angle, self, ttl,
                                      velocity, self.stage, self.image_map, self.collision_grid,
                                      CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                      self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet_2)
            elif self.stats.guns_rank > 2:
                heading_len = math.sqrt(heading.x ** 2 + heading.y ** 2)
                normal_heading = [heading.x / heading_len, heading.y / heading_len]
                left_gun_pos = pygame.math.Vector2(self.position.x + (normal_heading[1] * 15) - (normal_heading[0] * 6),
                                        self.position.y - (normal_heading[0] * 15) - (normal_heading[1] * 6))
                right_gun_pos = pygame.math.Vector2(self.position.x - (normal_heading[1] * 15) - (normal_heading[0] * 6),
                                         self.position.y + (normal_heading[0] * 15) - (normal_heading[1] * 6))
                new_bullet_1 = Bullet(left_gun_pos, heading, angle, self, ttl,
                                      velocity, self.stage, self.image_map, self.collision_grid,
                                      CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                      self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet_1)
                new_bullet_2 = Bullet(right_gun_pos, heading, angle, self, ttl,
                                      velocity, self.stage, self.image_map, self.collision_grid,
                                      CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                      self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet_2)
                new_bullet_3 = Bullet(position, heading, angle, self, ttl,
                                      velocity, self.stage, self.image_map, self.collision_grid,
                                      CollisionType.BULLETS, [CollisionType.ROCK, CollisionType.AI_SHIPS],
                                      self.stats.guns_rank, self.all_sprites)
                self.bullets.append(new_bullet_3)

            return True

    def fire_missile2(self, heading, missile_range, velocity, angle, target, rock_list):
        position = pygame.math.Vector2(self.position.x, self.position.y)
        new_missile = Missile(self.stage, position, heading, self, missile_range,
                              velocity, angle, target, rock_list, self.image_map,
                              self.collision_grid, self.all_sprites)
        self.missiles.append(new_missile)
        return True
