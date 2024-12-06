from __future__ import annotations

import logging

import pygame

from pygamengn.class_registrar import ClassRegistrar
from pygamengn.game_object_base import GameObjectBase



@ClassRegistrar.register("ImageAsset")
class ImageAsset(GameObjectBase):
    """Loadable image asset."""

    def __init__(self, fname: str, cache_rotations: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.__fname = fname
        self.__cache_rotations = cache_rotations
        self.__base_surface = pygame.image.load(self.__fname).convert_alpha()
        self.__scaled_rotations = {}
        if self.__cache_rotations:
            self.__scaled_rotations[1] = [self.__base_surface].extend(
                [pygame.transform.rotate(self.__base_surface, i) for i in range(1, 360)]
            )
        else:
            self.__scaled_rotations[1] = [self.__base_surface]


    @property
    def surface(self) -> pygame.Surface:
        """Returns the image with 0-degree rotation and scale of 1."""
        return self.__base_surface


    def get_surface(self, rotation: int = 0, scale: float = 1.0):
        """Returns the image at the given rotation and scale."""
        try:
            return self.__scaled_rotations[scale][rotation]

        except KeyError:
            logging.warn(f"ImageAsset '{self.__fname}': Scale {scale} is not cached.")
            return None

        except IndexError:
            logging.warn(f"ImageAsset '{self.__fname}': Rotation angle {rotation} is not cached.")
            return None


    def cache_scale(self, scale: float):
        """Caches the image at the given scale."""
        if not scale in self.__scaled_rotations:
            if self.__cache_rotations:
                self.__scaled_rotations[scale] = [
                    pygame.transform.rotozoom(self.__base_surface, i, scale) for i in range(360)
                ]
            else:
                self.__scaled_rotations[scale] = [self.__base_surface.smoothscale_by(scale)]
        else:
            logging.warn(f"ImageAsset '{self.__fname}': Scale {scale} is already cached.")
