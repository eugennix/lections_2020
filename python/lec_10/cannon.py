import numpy as np
import pygame as pg
from random import randint
import colors


pg.init()
pg.font.init()

SCREEN_SIZE = (800, 600)


def rand_color():
    return randint(0, 255), randint(0, 255), randint(0, 255)


class Coord:
    """
    For coordinates
    """

    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y


class Velocity:
    """
    For velocity
    """

    def __init__(self, dx: int = 0, dy: int = 0):
        self.dx = dx
        self.dy = dy


class GameObject:
    """
    Common class for all screen objects
    """

    def __init__(self, coord: Coord = Coord(),
                 velocity: Velocity = Velocity(), radius=0, color=None):
        self.coord = coord
        self.velocity = velocity
        if color is None:
            color = rand_color()
        self.color = color
        self.rad = radius
        self.is_alive = True

    def move(self, time=1, gravity=0):
        """
        Moves the ball according to it's velocity and time step.
        Changes the ball's velocity due to gravitational force.
        """
        self.velocity.dy += gravity
        self.coord.x += self.velocity.dx
        self.coord.y += self.velocity.dy
        self.check_corners()

    def check_corners(self, refl_ort=0.8, refl_par=0.9):
        """
        Reflects ball's velocity when ball bumps into the screen corners.
        Implements inelastic rebounds.
        """
        if self.coord.x < self.rad:
            self.coord.x = self.rad
            self.velocity.dx = -int(self.velocity.dx * refl_ort)
            self.velocity.dy = int(self.velocity.dy * refl_par)
        elif self.coord.x > SCREEN_SIZE[0] - self.rad:
            self.coord.x = SCREEN_SIZE[0] - self.rad
            self.velocity.dx = -int(self.velocity.dx * refl_ort)
            self.velocity.dy = int(self.velocity.dy * refl_par)

        if self.coord.y < self.rad:
            self.coord.y = self.rad
            self.velocity.dy = -int(self.velocity.dy * refl_ort)
            self.velocity.dx = int(self.velocity.dx * refl_par)
        elif self.coord.y > SCREEN_SIZE[1] - self.rad:
            self.coord.y = SCREEN_SIZE[1] - self.rad
            self.velocity.dy = -int(self.velocity.dy * refl_ort)
            self.velocity.dx = int(self.velocity.dx * refl_par)


class Shell(GameObject):
    """
    The ball class. Creates a ball, controls it's movement
    and implement it's rendering.
    """

    def __init__(self, coord: Coord = Coord(), velocity:
                 Velocity = Velocity(), rad=20, color=None):
        super().__init__(coord, velocity, rad, color)

    def move(self, time=1, gravity=0):
        """
        Moves the ball according to it's velocity and time step.
        Changes the ball's velocity due to gravitational force.
        """
        super().move(time, gravity)
        if self.velocity.dx ** 2 + self.velocity.dy ** 2 < 2 ** 2 \
                and self.coord.y > SCREEN_SIZE[1] - 2 * self.rad:
            self.is_alive = False

    def draw(self, screen):
        """
        Draws the ball on appropriate surface.
        """
        pg.draw.circle(screen, self.color,
                       (self.coord.x, self.coord.y), self.rad)


class Cannon(GameObject):
    """
    Cannon class. Manages it's rendering, movement and striking.
    """

    def __init__(self, coord: Coord = Coord(30, SCREEN_SIZE[1] // 2), angle=0,
                 max_pow=50, min_pow=10, color=colors.RED):
        """
        Constructor method. Sets coordinate, direction,
        minimum and maximum power and color of the gun.
        """
        super().__init__(coord, color=color)
        self.angle = angle
        self.max_pow = max_pow
        self.min_pow = min_pow
        self.active = False
        self.pow = min_pow

    def activate(self):
        """
        Activates gun's charge.
        """
        self.active = True

    def gain(self, inc=2):
        """
        Increases current gun charge power.
        """
        if self.active and self.pow < self.max_pow:
            self.pow += inc

    def strike(self):
        """
        Creates ball, according to gun's direction and current charge power.
        """
        vel = self.pow
        angle = self.angle
        ball = Shell(Coord(self.coord.x, self.coord.y),
                     Velocity(int(vel * np.cos(angle)), int(vel * np.sin(angle))))
        self.pow = self.min_pow
        self.active = False
        return ball

    def set_angle(self, target_pos):
        """
        Sets gun's direction to target position.
        """
        self.angle = np.arctan2(target_pos[1] - self.coord.y,
                                target_pos[0] - self.coord.y)

    def shift_position(self, inc):
        """
        Changes vertical position of the gun.
        :param inc: смещение пушки по вертикали
        """
        if (self.coord.y > 30 or inc > 0) and (self.coord.y < SCREEN_SIZE[1] - 30 or inc < 0):
            self.coord.y += inc

    def draw(self, screen):
        """
        Draws the gun on the screen.
        """
        gun_shape = []
        vec_1 = np.array([int(5 * np.cos(self.angle - np.pi / 2)), int(5 * np.sin(self.angle - np.pi / 2))])
        vec_2 = np.array([int(self.pow * np.cos(self.angle)), int(self.pow * np.sin(self.angle))])
        gun_pos = np.array([self.coord.x, self.coord.y])
        gun_shape.append((gun_pos + vec_1).tolist())
        gun_shape.append((gun_pos + vec_1 + vec_2).tolist())
        gun_shape.append((gun_pos + vec_2 - vec_1).tolist())
        gun_shape.append((gun_pos - vec_1).tolist())
        pg.draw.polygon(screen, self.color, gun_shape)


class Target(GameObject):
    """
    Target class. Creates target,
    manages it's rendering and collision with a ball event.
    """

    def __init__(self, coord: Coord = None,
                 velocity: Velocity = Velocity(0, 0), rad=None, color=None):
        """
        Constructor method. Sets coordinate, color and radius of the target.
        """
        if rad is None:
            rad = randint(20, 50)
        if coord is None:
            coord = Coord(randint(rad, SCREEN_SIZE[0] - rad),
                          randint(rad, SCREEN_SIZE[1] - rad))
        super().__init__(coord, velocity, rad, color)

    def check_collision(self, ball):
        """
        Checks whether the ball bumps into target.
        """
        dist = ((self.coord.x - ball.coord.x) ** 2 +
                (self.coord.y - ball.coord.y) ** 2) ** 0.5
        min_dist = self.rad + ball.rad
        return dist <= min_dist

    def draw(self, screen):
        """
        Draws the target on the screen
        """
        pg.draw.circle(screen, self.color,
                       (self.coord.x, self.coord.y), self.rad)
        pg.draw.circle(screen,
                       (self.color[0]//2, self.color[1]//2, self.color[2]//2),
                       (self.coord.x, self.coord.y), self.rad//2)


class MovingTarget(Target):
    def __init__(self, coord: Coord = None, velocity: Velocity = None,
                 color=None, rad=None):
        if velocity is None:
            velocity = Velocity(randint(-7, +7), randint(-5, +5))
        super().__init__(coord, velocity, rad, color)


class ScoreTable:
    """
    Score table class.
    """

    def __init__(self, t_destr=0, b_used=0):
        self.t_destr = t_destr
        self.b_used = b_used
        self.font = pg.font.SysFont("dejavusansmono", 25)

    def score(self):
        """
        Score calculation method.
        """
        return self.t_destr - self.b_used

    def draw(self, screen):
        score_surf = [
            self.font.render("Destroyed: {}".format(self.t_destr), True, colors.WHITE),
            self.font.render("Balls used: {}".format(self.b_used), True, colors.WHITE),
            self.font.render("Total: {}".format(self.score()), True, colors.RED),
        ]
        for i in range(3):
            screen.blit(score_surf[i], [10, 10 + 30 * i])


class Manager:
    """
    Class that manages events' handling, ball's motion and collision, target creation, etc.
    """

    def __init__(self, n_targets=1):
        self.balls = []
        self.gun = Cannon()
        self.targets = []
        self.score_t = ScoreTable()
        self.n_targets = n_targets
        self.new_mission()

    def new_mission(self):
        """
        Adds new targets.
        """
        self.balls = []
        for i in range(self.n_targets):
            self.targets.append(Target())
        for i in range(self.n_targets + 2):
            self.targets.append(MovingTarget())

    def process(self, events, screen):
        """
        Runs all necessary method for each iteration. Adds new targets, if previous are destroyed.
        """
        done = self.handle_events(events)

        if pg.mouse.get_focused():
            mouse_pos = pg.mouse.get_pos()
            self.gun.set_angle(mouse_pos)

        self.move()
        self.collide()
        self.draw(screen)

        if len(self.targets) == 0:
            self.new_mission()

        return done

    def handle_events(self, events):
        """
        Handles events from keyboard, mouse, etc.
        """
        need_exit = False
        for event in events:
            if event.type == pg.QUIT:
                need_exit = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.gun.shift_position(-5)
                elif event.key == pg.K_DOWN:
                    self.gun.shift_position(5)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.gun.activate()
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.balls.append(self.gun.strike())
                    self.score_t.b_used += 1
        return need_exit

    def draw(self, screen):
        """
        Runs balls', gun's, targets' and score table's drawing method.
        """
        for ball in self.balls:
            ball.draw(screen)
        for target in self.targets:
            target.draw(screen)
        self.gun.draw(screen)
        self.score_t.draw(screen)

    def move(self):
        """
        Runs balls' and gun's movement method, removes dead balls.
        """
        dead_balls = []
        for i, ball in enumerate(self.balls):
            ball.move(gravity=2)
            if not ball.is_alive:
                dead_balls.append(i)
        for i in reversed(dead_balls):
            self.balls.pop(i)
        for i, target in enumerate(self.targets):
            target.move()
        self.gun.gain()

    def collide(self):
        """
        Checks whether balls bump into targets, sets balls' alive trigger.
        """
        collisions = []
        targets_c = []
        for i, ball in enumerate(self.balls):
            for j, target in enumerate(self.targets):
                if target.check_collision(ball):
                    collisions.append([i, j])
                    targets_c.append(j)
        targets_c.sort()
        for j in reversed(targets_c):
            self.score_t.t_destr += 1
            self.targets.pop(j)


game_screen = pg.display.set_mode(SCREEN_SIZE)
pg.display.set_caption("The gun of Khiryanov")

terminate_program = False
clock = pg.time.Clock()

mgr = Manager(n_targets=3)

while not terminate_program:
    clock.tick(15)
    game_screen.fill(colors.BLACK)

    terminate_program = mgr.process(pg.event.get(), game_screen)

    pg.display.flip()

pg.quit()
