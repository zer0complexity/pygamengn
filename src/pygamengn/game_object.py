import pygame

from pygamengn.blit_surface import BlitSurface
from pygamengn.class_registrar import ClassRegistrar
from pygamengn.game_object_base import GameObjectBase
from pygamengn.geometry import normalize_angle
from pygamengn.network.replicated_property import ReplicatedProperty
from pygamengn.transform import Transform


@ClassRegistrar.register("GameObject")
class GameObject(pygame.sprite.Sprite, GameObjectBase):
    """Basic game object."""

    def __init__(self,
                 image_asset,
                 is_collidable=True,
                 scale=1.0,
                 alpha=1.0,
                 visible=True,
                 heading=0,
                 death_effect=None,
                 damage=0,
                 kill_when_off_screen=False,
                 off_screen_ttl=0
    ):
        pygame.sprite.Sprite.__init__(self)
        GameObjectBase.__init__(self)

        self.image_asset = image_asset
        self.image = self.image_asset.surface if self.image_asset else None
        self.rect = self.image.get_rect() if self.image_asset else None
        self.scale = scale
        self.__pos = pygame.math.Vector2(0.0, 0.0)
        self.__heading = normalize_angle(round(heading))
        self._dirty_image = True
        self.is_collidable = is_collidable
        if self.is_collidable:
            self.mask = pygame.mask.from_surface(self.image, 16)
        else:
            self.mask = None
        self.parent = None
        self.health = 100
        self.attachments = []
        self.__alpha = alpha
        self.visible = visible
        self.death_effect = death_effect
        self.damage = damage
        self.kill_when_off_screen = kill_when_off_screen
        self.__off_screen_warning = False
        self.__off_screen_ms = 0
        self.__off_screen_ttl = off_screen_ttl

    def get_replicated_props(self):
        """Returns a list of properties that this object will replicate from server to connected clients."""
        return [
#             ReplicatedProperty("position", getter="position_tuple"),
            ReplicatedProperty("heading")
        ]

    def update(self, delta):
        """Updates the game object. Delta time is in ms."""
        super().update()

        if self.__off_screen_warning:
            self.__off_screen_ms -= delta
            if self.__off_screen_ms <= 0:
                # If an object is off the screen for its maximum allowed time to be off the screen (off_screen_ms),
                # then it and its attachments get killed, regardless of whether the attachments are off the screen.
                self.__kill_myself()
                return

        self.transform()
        for attachment in self.attachments:
            if attachment.parent_transform:
                t = Transform(self.position, self.heading)

                attachment_pos = t.apply(attachment.offset)
                attachment.game_object.position = attachment_pos
                attachment.game_object.heading = self.heading

    def transform(self):
        """Transforms the object based on current heading, scale, and position."""
        # Rotate and scale if necessary
        if self._dirty_image:
            self.image = self.image_asset.get_surface(self.__heading, self.scale)
            if self.__alpha != 1.0:
                self.image.set_alpha(self.__alpha * 255)
            self.rect = self.image.get_rect()
            if self.is_collidable:
                self.mask = pygame.mask.from_surface(self.image, 16)
            self._dirty_image = False

        # Translate
        topleft = self.position - pygame.math.Vector2(self.rect.width / 2.0, self.rect.height / 2.0)
        self.rect.topleft = pygame.Vector2(round(topleft.x), round(topleft.y))

    def set_scale(self, scale):
        """Sets the scale of the sprite."""
        self._dirty_image = self._dirty_image or self.scale != scale
        self.scale = scale

    @property
    def position(self):
        """Retrieves the gob's position."""
        return self.__pos

    @position.setter
    def position(self, pos):
        """Sets the position of the sprite in the screen so that the sprite's center is at pos."""
        self.__pos = pygame.math.Vector2(pos[0], pos[1])

    @property
    def position_tuple(self):
        """Retrieves the gob's position."""
        return (self.__pos.x, self.__pos.y)

    @property
    def heading(self):
        return self.__heading

    @heading.setter
    def heading(self, h):
        """Sets the orientation of the game object."""
        self._dirty_image = self._dirty_image or self.__heading != h
        self.__heading = normalize_angle(round(h))

    def set_image(self, image_asset):
        """Sets a new image for the game object."""
        self.image_asset = image_asset
        self.image = self.image_asset.surface
        self._dirty_image = True

    @property
    def alpha(self) -> float:
        return self.__alpha

    @alpha.setter
    def alpha(self, a: float):
        self._dirty_image = self._dirty_image or self.__alpha != a
        self.__alpha = a

    def attach(self, game_object, offset, take_parent_transform):
        """Attaches a game object to this game object at the given offset."""
        self.attachments.append(Attachment(game_object, offset, take_parent_transform))
        game_object.set_parent(self)

    def handle_collision(self, gob, world_pos):
        """Reacts to collision against game object gob."""
        # Apply damage to the collided sprite
        instigator = GameObject.get_root_parent(self)
        gob.take_damage(self.damage, instigator)

    def take_damage(self, damage, instigator):
        """Takes damage for this game object."""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.die(instigator)

    def die(self, instigator):
        """Die."""
        if self.alive() and self.death_effect:
            effect = self.death_effect.create()
            effect.position = self.position
            effect.play(self.death_effect_callback)

        # Kill off attachments
        for attachment in self.attachments:
            attachment.game_object.take_damage(attachment.game_object.health, instigator)

        self.kill()

    def add_to_groups(self, groups):
        """Adds the game object to the given sprite groups."""
        self.add(groups)

    def set_layer_id(self, layer_id):
        """Sets the layer for rendering."""
        self._layer = layer_id

    def set_parent(self, parent):
        """Sets this game object's parent."""
        self.parent = parent

    def death_effect_callback(self):
        """Callback for when the death effect is done playing."""
        pass

    @property
    def off_screen_warning(self) -> bool:
        return self.__off_screen_warning

    @off_screen_warning.setter
    def off_screen_warning(self, value: bool):
        self.__off_screen_warning = value
        if value:
            self.__off_screen_ms = self.__off_screen_ttl

    @property
    def off_screen_ms(self) -> int:
        return self.__off_screen_ms

    @property
    def blit_surfaces(self) -> list[BlitSurface]:
        return [BlitSurface(self.image, self.rect)]

    def __kill_myself(self):
        """Recursively kills this GameObject and its attachments."""
        for attachment in self.attachments:
            attachment.game_object.__kill_myself()
        self.attachments.clear()
        self.kill()

    @classmethod
    def get_root_parent(cls, gob):
        """Recurses up parent-child relationships to find the root parent."""
        root = gob
        while not root.parent is None:
            root = gob.parent
        return root


class Attachment():

    def __init__(self, game_object, offset, parent_transform):
        self.game_object = game_object
        self.offset = offset
        self.parent_transform = parent_transform
