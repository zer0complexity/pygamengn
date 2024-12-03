import pygame

from pygamengn.class_registrar import ClassRegistrar
from pygamengn.UI.panel import Panel



@ClassRegistrar.register("TexturePanel")
class TexturePanel(Panel):
    """
    Basic UI panel that shows an image.

    TODO: Setting an angle different than 0 rotates the TexturePanel's blit surface, but it doesn't correct the
          component's rectangle or its children's. The feature only works if both these conditions are true:

            1. The component has no children.
            2. The component's rectangle is only used internally by itself. Mouse interactions rely on the component's
               rectangle accurately representing its shape and orientation; those will behave badly.
    """

    def __init__(
        self,
        image_asset,
        fix_texture_aspect_ratio = True,
        scale_texture_to_rect = True,
        angle = 0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._image_asset = image_asset
        self._fix_texture_aspect_ratio = fix_texture_aspect_ratio
        self._scale_texture_to_rect = scale_texture_to_rect
        self._angle = angle
        self._angle_changed = True

    def _draw_surface(self):
        super()._draw_surface()
        if self._scale_texture_to_rect:
            # Fit the texture to the Component's rect, keeping original texture aspect ratio if required
            image_asset_rect = self._image_asset.get_rect()
            if self._fix_texture_aspect_ratio:
                surface_rect = image_asset_rect.fit(self.rect)
            else:
                surface_rect = self.rect
            self._surface = pygame.transform.rotozoom(
                self._image_asset,
                self._angle,
                min(
                    surface_rect.width / image_asset_rect.width,
                    surface_rect.height / image_asset_rect.height
                )
            )
        else:
            self._surface = pygame.transform.rotozoom(self._image_asset, self._angle, 1)

    @property
    def angle(self) -> float:
        return self.__angle

    @angle.setter
    def angle(self, alpha: float):
        if alpha != self._angle:
            self._angle = alpha
            self._angle_changed = True

    @property
    def _needs_redraw(self) -> bool:
        """Spinner redraws its surface on every frame."""
        return super()._needs_redraw or self._angle_changed

    def _reset_redraw_flags(self):
        super()._reset_redraw_flags()
        self._angle_changed = False