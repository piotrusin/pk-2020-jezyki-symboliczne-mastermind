"""
Main project file.
It contains App class that create most of the game objects
and register game events.
This is the place where main game loop is located (run() method).
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import glm
import pygame
import OpenGL.GL as GL

import game.gui
import game.logic
import game.model.feedback
import game.model.answer
import game.opengl_objects.sphere
import game.scene
import game.state
from mouse import Mouse
from events import Events, post
from camera import Camera

RESOLUTION = (1024, 768)
CAMERA_FRONT = glm.vec3(10.0, 40.0, 15.0)
ANSWERS_START_POS = glm.vec3(0.0, 0.0, 0.0)
ANSWERS_OFFSET = 2.5


# pylint: disable=too-many-instance-attributes
class App:
    """
    Core of the game application.
    This class creates most of the game objects and
    handles event listeners registration.
    It also contains the main game loop.
    """

    def __init__(self):
        self.window = pygame.display.set_mode(RESOLUTION, pygame.DOUBLEBUF | pygame.OPENGL)
        self.clock = pygame.time.Clock()
        self.mouse = Mouse()
        self.camera = Camera(CAMERA_FRONT)
        self.events = Events()
        self.state = game.state.State()
        self.logic = game.logic.Logic(state=self.state)
        self.gui = game.gui.Gui()
        self.scene = game.scene.Scene()

        sphere = game.opengl_objects.sphere.Sphere()

        for row in range(12):
            self.scene.add_child(
                game.model.feedback.Feedback(
                    row,
                    ANSWERS_START_POS,
                    ANSWERS_OFFSET,
                    self.state,
                    sphere
                )
            )
            self.scene.add_child(
                game.model.answer.Answer(
                    row,
                    ANSWERS_START_POS,
                    ANSWERS_OFFSET,
                    self.state,
                    sphere
                )
            )

    def register_events(self):
        """Register event listeners used in the application."""
        # handle mouse movement
        self.events.on(pygame.MOUSEMOTION, self.mouse.on_mouse_move)
        # register camera events for movement and zooming
        self.camera.register_event_listeners(self.events, self.mouse)
        # register SPACEBAR as active selection switcher
        self.events.on(
            pygame.KEYDOWN,
            lambda event: self.logic.change_active_index(),
            conditions={'key': pygame.K_SPACE}
        )
        # check answer after pressing return
        self.events.on(
            pygame.KEYDOWN,
            lambda event: self.logic.check_row(),
            conditions={'key': pygame.K_RETURN}
        )
        # draw scene before gui to avoid transparency issues
        self.events.on(Events.DRAW, self.scene.draw)
        # toggle controls texts visibility
        self.events.on(
            pygame.KEYDOWN,
            lambda event: self.gui.toggle_controls_visibility(),
            conditions={'key': pygame.K_TAB}
        )
        # draw gui
        self.events.on(Events.DRAW, lambda event: self.gui.draw())
        # bind keys 1-6 as selection changers
        keys_to_bind = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
        for index, key in enumerate(keys_to_bind):
            self.events.on(
                pygame.KEYDOWN,
                lambda event, data: self.logic.set_answer_digit(data['digit']),
                conditions={'key': key},
                data={'digit': index + 1}
            )

        self.events.on(
            pygame.KEYDOWN,
            lambda event: post(Events.CHEATER_CHECK, {'state': self.state}),
            conditions={'key': pygame.K_o}
        )
        self.events.on(Events.CHEATER_CHECK, lambda event: self.gui.on_cheater_check())
        self.events.on(Events.CHEATER_CHECK, lambda event: self.state.disable_input())

        # reset game after pressing R
        self.events.on(
            pygame.KEYDOWN,
            lambda event: self.state.reset(),
            conditions={'key': pygame.K_r}
        )
        # change game results texts to the new combination after game reset
        self.events.on(
            Events.AFTER_GAME_RESET,
            lambda event: self.gui.after_game_reset(event.state)
        )
        # hide previous game result after resetting the game
        self.events.on(Events.GAME_RESET, lambda event: self.gui.hide_result())
        # show result message and disable input when the game is won
        self.events.on(Events.GAME_WON, lambda event: self.gui.on_game_won())
        self.events.on(Events.GAME_WON, lambda event: self.state.disable_input())
        # show result message and disable input when the game is lost
        self.events.on(Events.GAME_OVER, lambda event: self.gui.on_game_over())
        self.events.on(Events.GAME_OVER, lambda event: self.state.disable_input())
        # quit the application after clicking X in the window
        self.events.on(pygame.QUIT, lambda event: self.quit())
        # quit the application after pressing ESC key
        self.events.on(
            pygame.KEYDOWN,
            lambda event: self.quit(),
            conditions={'key': pygame.K_ESCAPE}
        )

    def run(self):
        """Main game loop."""

        last_frame = 0
        aspect_ratio = RESOLUTION[0] / RESOLUTION[1]

        while True:
            GL.glClearColor(0.0, 0.0, 0.0, 1.0)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            self.events.process(pygame.event.get())

            current_frame = pygame.time.get_ticks() / 1000.0
            post(Events.DRAW, {
                'dt': current_frame - last_frame,
                'resolution': RESOLUTION,
                'camera': self.camera,
                'view': glm.lookAt(
                    self.camera.pos,
                    self.camera.pos + self.camera.front,
                    self.camera.up
                ),
                'projection': glm.perspective(
                    glm.radians(self.camera.zoom),
                    aspect_ratio,
                    0.1,
                    100.0
                )
            })
            last_frame = current_frame

            pygame.display.flip()
            self.clock.tick(60)

    @staticmethod
    def quit():
        """Quit the application."""
        pygame.quit()
        sys.exit()


def main():
    """
    Wrapper function executed directly after starting the program.
    It is used to create App class, and to run the application.
    It also set OpenGL constants used in the game.
    """
    pygame.init()

    app = App()

    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_BLEND)  # blend is used in GUI texts
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    app.register_events()
    app.run()


if __name__ == '__main__':
    main()
