import logging

import pygame

from pygamengn.class_registrar import ClassRegistrar

from pygamengn.UI.root import Root


@ClassRegistrar.register("Hud")
class Hud(Root):
    """HUD UI."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.heading = 0
        self._joystick_finger = -1
        self._fire = False
        self.__zero_angle = pygame.Vector2(1, 0)
        self._joystick_motion = False
        self._pause_callback = None


    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handles the given input event."""
        rv = False

        if self.joystick.active:
            if event.type == pygame.FINGERDOWN:
                if event.x < 0.4:
                    self._update_heading(event.x, event.y, True)
                    self._joystick_finger = event.finger_id
                else:
                    component_rect = self._component.rect
                    if self.pause_button.process_mouse_event(
                        pygame.Vector2(event.x * component_rect.width, event.y * component_rect.height),
                        event.type
                    ):
                        self._pause_callback()
                        self.joystick.set_visible(False)
                    else:
                        pos = self.button._normalized_pos
                        if event.x >= pos.x * 0.9 and event.y >= pos.y * 0.9 :
                            self._fire = True
                rv = True

            elif event.type == pygame.FINGERUP:
                if event.finger_id == self._joystick_finger:
                    self._joystick_finger = -1
                    self._joystick_motion = False
                rv = True

            elif event.type == pygame.FINGERMOTION:
                if event.finger_id == self._joystick_finger:
                    self._update_heading(event.x, event.y)
                    self._joystick_motion = True
                rv = True

        return rv


    def _update_heading(self, x: int, y: int, in_stick_panel: bool = False):
        finger_pos = pygame.Vector2(
            x * self._component.rect.width,
            y * self._component.rect.height
        )
        diff = finger_pos - pygame.Vector2(self.stick.rect.center)
        if not in_stick_panel or diff.magnitude() < self.stick.rect.width / 2:
            theta = self.__zero_angle.angle_to(diff)
            self.heading = -theta - 90
            self.ship.angle = self.heading


    @property
    def joystick_motion(self) -> bool:
        return self._joystick_motion


    @property
    def touch_joystick_active(self) -> bool:
        return self.joystick.active


    @property
    def fire(self) -> bool:
        """
        Returns True if there was fire input.

        Because the fire action is single shot, the underlying variable is set to false after a True value is returned.
        """
        rv = self._fire
        self._fire = False
        return rv


    def fade_in(self, duration: int):
        super().fade_in(duration)
        self._joystick_motion = False
        self._joystick_finger = -1
        self._fire = False


    def set_joystick_state(self, state: bool):
        self.joystick.active = state
        self.joystick.set_visible(state)


    def set_pause_callback(self, pause_callback):
        self._pause_callback = pause_callback


    def reset_heading(self):
        self.ship.angle = 0
        self.heading = 0
