# import all the libraries and other code files we will need
from game.ship import *
from game.stage import *
from game.badies import *
from game.input_manager import *
from game.sound_manager import *
from game.title_screen import *

from game.pick_up import PickUpSpawner
from game.high_scores import reload_characters, HighScoreEntry, Character
from collision.collision_grid import CollisionGrid


class StarshipRutlishGame:

    def play_game(self):
        # create a clock to use for timing
        clock = pygame.time.Clock()        

        running = True
        while running: 

            time_delta = clock.tick(60) / 1000.0
            self.saucer_timer += time_delta

            self.game_state = self.input_manager.check_for_game_state_input_events(pygame.event.get(), self.game_state)
            self.all_sprites.update(time_delta)

            self.check_collisions()
            self.stage.screen.blit(self.stage.star_field_image, (0, 0))
            self.all_sprites.draw(self.stage.screen)

            self.run_alien_saucer_logic()  # checks if it is time to create a new alien saucer
            self.display_score_and_missiles()  # draws the current player score and missile count on our frame
            self.check_score()   # awards an extra life each time the player has earned 10,000 points

            # Switch between all the game 'states' based on what is happening
            if self.game_state == 'start_playing':
                self.initialise_game()
            elif self.game_state == 'playing':  # normal state while player is in control shooting asteroids
                self.playing_game()
            elif self.game_state == 'exploding':  # handle player ship dying
                self.player_exploding()
            elif self.game_state == 'title_screen':  # switch to title menu state
                if self.input_manager.shouldSaveNewHighScore:
                    self.input_manager.shouldSaveNewHighScore = False
                    new_score = Character()
                    new_score.name = self.input_manager.current_string
                    new_score.stage = self.stats.stage
                    new_score.score = self.stats.score
                    new_score.save()
                    self.title_menu.high_scores = reload_characters(self.title_menu.high_scores)
                if self.input_manager.high_score_key_pressed:
                    self.title_menu.show_high_score_table = True
                else:
                    self.title_menu.show_high_score_table = False
                self.title_menu.display_title_menu_text()
            elif self.game_state == 'new_high_score':
                self.high_score_entry.display(self.input_manager.current_string)
            elif self.game_state == 'quit':
                running = False

            if time_delta > 0.0:
                fps_string = "FPS: " + "{:.2f}".format(1.0/time_delta)
                fps_text_render = self.fonts[0].render(fps_string, True, pygame.Color("#FFFFFF"))
                self.stage.screen.blit(fps_text_render, fps_text_render.get_rect(centerx=640, centery=30))

            pygame.display.flip()
        pygame.quit()

    def __init__(self):

        self.game_stats_text_color = pygame.color.Color('#FFFFFF')
        self.debris_colour = pygame.color.Color('#FFFFFF')
        self.ship_debris_colour = pygame.color.Color('#999999')

        # sets up the size of the game window for us to draw graphics into, also lets us set the game title text
        self.stage = Stage('Starship Rutlish 5', (1280, 640))

        self.fonts = []
        self.fonts.append(pygame.font.Font("data/fonts/AGENCYB.TTF", 30))
        self.fonts.append(pygame.font.Font("data/fonts/AmaticaSC-Regular.ttf", 50))
        self.fonts.append(pygame.font.Font("data/fonts/AmaticaSC-Regular.ttf", 150))

        self.image_map = pygame.image.load("data/graphics_map.png").convert_alpha()

        self.sound_manager = SoundManager()
        self.input_manager = InputManager()
        
        self.title_menu = TitleScreen(self.stage, self.fonts)
        self.high_score_entry = HighScoreEntry(self.stage, self.fonts)
        
        self.game_state = "title_screen"

        grid_size = 256
        screen_filling_number_of_grid_squares = [int(self.stage.width / grid_size), int(self.stage.height / grid_size)]
        self.collision_grid = CollisionGrid(screen_filling_number_of_grid_squares, grid_size)

        self.debris_surface = pygame.Surface((1, 1))
        self.debris_surface.fill(self.debris_colour)
        self.rock_sprite_table = self.load_asteroid_tile_table(self.image_map, 64, 64)
        self.all_sprites = pygame.sprite.OrderedUpdates()
        self.pick_up_spawner = None
        self.rock_list = []  # list containing all the currently active rocks
        self.num_rocks = 3
        self.next_life = 10000
        self.create_rocks(self.num_rocks)
        self.saucer = None
        self.saucer_timer = 0.0
        self.stats = Stats()
        self.stage.current_player_ship_stats = self.stats
        self.ship = None
        self.exploding_count = 0
        self.exploding_ttl = 180

    # This function is called each time you start playing by pressing a key on the title screen,
    # it resets the enemies and rocks and the player's ship  
    def initialise_game(self):
        self.game_state = 'playing'

        if self.saucer is not None: 
            self.kill_saucer()

        self.stats = Stats()
        self.stage.current_player_ship_stats = self.stats

        for rock in self.rock_list:
            rock.die()
        self.rock_list = []

        for sprite in self.all_sprites.sprites():
            sprite.kill()
        self.all_sprites.empty()

        self.num_rocks = 3
        self.next_life = 10000

        self.create_new_ship()  # this creates a new ship

        self.pick_up_spawner = PickUpSpawner(self.all_sprites,
                                             self.image_map, self.collision_grid)
        
        self.create_rocks(self.num_rocks)
        self.saucer_timer = 0
    
    # This is called each time we need to create a new player ship.
    # For example at the start of a new game or after the ship has exploded and you still have extra lives left
    def create_new_ship(self):

        self.ship = Ship(self.stage, self.input_manager, self.sound_manager,
                         self.stats, self.image_map, self.collision_grid,
                         self.ship_debris_colour, top_speed=10, acceleration=0.2, all_sprites=self.all_sprites)
        self.stage.current_player_ship = self.ship

    # checks if it's time to create a new alien saucer to attack the player
    # and gets rid of saucers that have overstayed their welcome      
    def run_alien_saucer_logic(self):
        # get rid of any saucers that have been around for a long time       
        if self.saucer is not None:            
            if self.saucer.laps >= 2:
                self.kill_saucer()
        
        # Check if it's time to create a saucer
        time_for_saucer = False
        if self.saucer_timer > 40.0:  # every forty seconds
            self.saucer_timer = 0
            time_for_saucer = True

        if self.saucer is None and time_for_saucer:
            self.create_alien_saucer()

    # this function finds a target for the player ship's 'homing' missile.
    # it does this by looping through all the rocks on the screen and finding 
    # which one is closest to the player and setting that as the target.
    def find_nearest_missile_target_to_ship(self):

        found_target = None
        self.ship.rockList = self.rock_list
        shortest_distance = 100000000.0

        if self.saucer is not None:
            distance = self.calculate_distance(self.ship, self.saucer)
            if distance < shortest_distance:
                shortest_distance = distance
                found_target = self.saucer

        # loop through all the rocks, find the one that is closest to the ship and make that
        # our missile target
        for rock in self.rock_list:
            distance = self.calculate_distance(self.ship, rock)
            if distance < shortest_distance:
                shortest_distance = distance
                found_target = rock

        return found_target

    # game logic that only runs while normal game play is happening. 
    # i.e. the player isn't exploding or still on the title screen                                           
    def playing_game(self):
        # out of lives, so switch to game title screen
        if self.stats.lives == 0:
            if self.check_new_high_score():
                self.game_state = 'new_high_score'
                
            else:
                self.game_state = 'title_screen'
        else:
            self.ship.update_rock_list(self.rock_list)
            self.ship.set_missile_target(self.find_nearest_missile_target_to_ship())
            self.ship.process_input_events()

            if len(self.rock_list) == 0:
                self.level_up()
          
    # game logic run when the player is still exploding after hitting an asteroid or a bullet   
    def player_exploding(self):
        self.exploding_count += 1
        if self.exploding_count > self.exploding_ttl:
            self.game_state = 'playing'
            if self.stats.lives == 0:
                self.ship.visible = False
            else:
                self.create_new_ship()
    
    # Each time the player clears all the rocks a new 'level' starts with more rocks 
    # the number of rocks is increased here and then created 
    def level_up(self):
        self.stats.stage += 1
        self.num_rocks += 1
        self.create_rocks(self.num_rocks)

    # displays the current player score
    def display_score_and_missiles(self):
        
        missile_count = 0
        if self.ship is not None:
            missile_count = self.ship.missile_count
        score_str = 'Missiles: {:d}    Score: {:,}    Stage: {:d}'.format(missile_count, self.stats.score,
                                                                          self.stats.stage)
    
        score_text = self.fonts[0].render(score_str, True, self.game_stats_text_color)
        score_text_rect = score_text.get_rect(x=25, centery=25)
        self.stage.screen.blit(score_text, score_text_rect)

        lives_count = 0
        if self.ship is not None:
            lives_count = self.stats.lives
        lives_str = 'Lives: {:d}'.format(lives_count)
        lives_text = self.fonts[0].render(lives_str, True, self.game_stats_text_color)
        lives_text_rect = lives_text.get_rect(right=self.stage.width-25, centery=25)
        self.stage.screen.blit(lives_text, lives_text_rect)

        guns_rank = 0
        if self.ship is not None:
            guns_rank = self.stats.guns_rank
        if guns_rank == 5:
            guns_rank_str = 'Guns Rank: MAX'
        else:
            guns_rank_str = 'Guns Rank: {:d}'.format(guns_rank)
        guns_rank_text = self.fonts[0].render(guns_rank_str, True, self.game_stats_text_color)
        guns_rank_text_rect = guns_rank_text.get_rect(right=self.stage.width-400, centery=25)
        self.stage.screen.blit(guns_rank_text, guns_rank_text_rect)

        missiles_rank = 0
        if self.ship is not None:
            missiles_rank = self.stats.missiles_rank
        if missiles_rank == 3:
            missiles_rank_str = 'Missiles Rank: MAX'
        else:
            missiles_rank_str = 'Missiles Rank: {:d}'.format(missiles_rank)
         
        missiles_rank_text = self.fonts[0].render(missiles_rank_str, True, self.game_stats_text_color)
        missiles_rank_text_rect = missiles_rank_text.get_rect(right=self.stage.width-200, centery=25)
        self.stage.screen.blit(missiles_rank_text, missiles_rank_text_rect)

    # Check for ship hitting the rocks etc.
    def check_collisions(self):

        self.collision_grid.update_shape_grid_positions()
        self.collision_grid.check_collisions()

        # Rocks
        for rock in self.rock_list:

            if len(rock.collision_circle.collided_shapes_this_frame) > 0:
                if self.rock_list.count(rock) != 0:
                    rock.try_pick_up_spawn(self.pick_up_spawner)
                    self.rock_list.remove(rock)
                    rock.die()

                if rock.collision_circle.collided_shapes_this_frame[0].game_type == CollisionType.BULLETS or \
                        rock.collision_circle.collided_shapes_this_frame[0].game_type == CollisionType.PLAYER or \
                        rock.collision_circle.collided_shapes_this_frame[0].game_type == CollisionType.BOMB:
                    if rock.rock_type == Rock.large_rock_type:
                        self.sound_manager.play_sound("explode1")
                        new_rock_type = Rock.medium_rock_type
                        self.stats.score += 50
                    elif rock.rock_type == Rock.medium_rock_type:
                        self.sound_manager.play_sound("explode2")
                        new_rock_type = Rock.small_rock_type
                        self.stats.score += 100
                    else:
                        self.sound_manager.play_sound("explode3")
                        new_rock_type = None
                        self.stats.score += 200
                    
                    if rock.rock_type != Rock.small_rock_type:
                        # new rocks
                        for _ in range(0, 2):
                            position = pygame.math.Vector2(rock.position.x, rock.position.y)
                                           
                            new_rock = Rock(self.stage, position, new_rock_type,
                                            self.rock_sprite_table, self.all_sprites, self.collision_grid)
                            self.rock_list.append(new_rock)

                elif rock.collision_circle.collided_shapes_this_frame[0].game_type == CollisionType.MISSILES or \
                        rock.collision_circle.collided_shapes_this_frame[0].game_type == CollisionType.BOMB_EXPLOSION:
                    if rock.rock_type == Rock.large_rock_type:
                        self.sound_manager.play_sound("explode1")
                        new_rock_type = Rock.small_rock_type
                        self.stats.score += 250

                        for _ in range(0, 4):
                            position = pygame.math.Vector2(rock.position.x, rock.position.y)
                            new_rock = Rock(self.stage, position, new_rock_type,
                                            self.rock_sprite_table, self.all_sprites, self.collision_grid)
                            self.rock_list.append(new_rock)

                    elif rock.rock_type == Rock.medium_rock_type:
                        self.sound_manager.play_sound("explode2")
                        self.stats.score += 500
                    else:
                        self.sound_manager.play_sound("explode3")
                        self.stats.score += 200
                            
                self.create_debris(rock)

        if self.saucer is not None and len(self.saucer.collision_shape.collided_shapes_this_frame) > 0:
            if self.saucer.collision_shape.collided_shapes_this_frame[0].game_type == CollisionType.BULLETS or \
                    self.saucer.collision_shape.collided_shapes_this_frame[0].game_type == CollisionType.MISSILES:
                self.stats.score += self.saucer.score_value
                self.saucer.try_pick_up_spawn(self.pick_up_spawner)

            self.create_debris(self.saucer)
            self.kill_saucer()

        if self.ship is not None and len(self.ship.collision_shape.collided_shapes_this_frame) > 0:
            if self.ship.collision_shape.collided_shapes_this_frame[0].game_type == CollisionType.PICK_UP:
                pass
            elif not self.ship.is_shield_active:
                self.kill_ship()

    # game logic run immediately when player dies putting the game into the 'exploding' state 
    def kill_ship(self):
        self.sound_manager.stop_sound("thrust")
        self.sound_manager.play_sound("explode2")
        self.exploding_count = 0
        self.stats.lives -= 1
        self.stats.downgrade_guns()
        self.stats.downgrade_missiles()
                         
        self.game_state = 'exploding'
        self.ship.die()
    
    # kills an alien saucer
    def kill_saucer(self):
        self.sound_manager.stop_sound("l_saucer")
        self.sound_manager.stop_sound("s_saucer")
        self.sound_manager.play_sound("explode2")
        self.saucer.die()
        self.saucer = None
    
    # creates debris from an exploding rock or saucer
    def create_debris(self, sprite):
        for _ in range(0, 30):
            position = pygame.math.Vector2(sprite.position.x, sprite.position.y)
            Debris(position, self.debris_surface, self.all_sprites)

    def check_score(self):
        if self.stats.score > 0 and self.stats.score > self.next_life:
            self.sound_manager.play_sound("extra_life")
            self.next_life += 10000
            self.stats.lives += 1

    def check_new_high_score(self):
        new_high_score = False
        high_scores = []
        high_scores = reload_characters(high_scores)
        if len(high_scores) < 10:
            new_high_score = True
        else:
            player_num = 1
            for high_player in high_scores:
                if player_num < 11:
                    if self.stats.score > high_player.score:
                        new_high_score = True
                player_num += 1
        return new_high_score

    # create an alien saucer
    def create_alien_saucer(self):
        rand_val = random.randrange(0, 10)
        if rand_val <= 3:
            self.saucer = Saucer(self.stage, Saucer.small_saucer_type, self.ship,
                                 self.sound_manager, self.image_map,
                                 self.collision_grid, self.all_sprites)
        else:
            self.saucer = Saucer(self.stage, Saucer.large_saucer_type, self.ship,
                                 self.sound_manager, self.image_map,
                                 self.collision_grid, self.all_sprites)

    # Create all the initial rocks that you will have to destroy to get to the next stage
    def create_rocks(self, number_of_rocks):

        # run this code for every rock we want to create. 'numberOfRocks' is how many rocks   
        for rockNumber in range(0, number_of_rocks):

            # choose a random position on the screen to place the rock.
            position = pygame.math.Vector2(random.randrange(-10, 10), random.randrange(-10, 10))
            
            # create the rock with our position and pick the 'large' type of rock.
            new_rock = Rock(self.stage, position, Rock.large_rock_type,
                            self.rock_sprite_table, self.all_sprites, self.collision_grid)

            # add the rock to our list of all rocks
            self.rock_list.append(new_rock)

    # calculates the distance between two objects
    def calculate_distance(self, start_object, finish_object):
        # check normal screen x distance
        x_normal_dist = start_object.position.x - finish_object.position.x
        x_normal_dist_squared = x_normal_dist ** 2

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
        y_normal_dist_squared = y_normal_dist * y_normal_dist

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

        distance = (x_dist_final + y_dist_final) ** 0.5

        return distance

    @staticmethod
    def load_asteroid_tile_table(image_map, width, height):
        image_width = 320
        image_height = 384
        tile_table = []
        for tile_y in range(0, int(image_height/height)):
            line = []
            tile_table.append(line)
            for tile_x in range(0, int(image_width/width)):
                rect = (tile_x*width, tile_y*height, width, height)
                line.append(image_map.subsurface(rect))
        return tile_table


class Stats:
    def __init__(self):
        self.lives = 3
        self.score = 0
        self.stage = 1
        self.guns_rank = 1
        self.missiles_rank = 1

    def upgrade_guns(self):
        self.guns_rank += 1
        if self.guns_rank > 5:
            self.guns_rank = 5

    def downgrade_guns(self):
        self.guns_rank -= 1
        if self.guns_rank < 1:
            self.guns_rank = 1

    def upgrade_missiles(self):
        self.missiles_rank += 1
        if self.missiles_rank > 3:
            self.missiles_rank = 3

    def downgrade_missiles(self):
        self.missiles_rank -= 1
        if self.missiles_rank < 1:
            self.missiles_rank = 1


# We actually create the game class and run the game loop here
if __name__ == '__main__':
    game = StarshipRutlishGame()
    game.play_game()
