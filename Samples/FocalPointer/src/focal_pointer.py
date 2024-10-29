import pygame
import pygamengn

from photo import Photo


@pygamengn.ClassRegistrar.register("FocalPointer")
class FocalPointer(pygamengn.Game):

    def __init__(self, images, photo_type_spec, **kwargs):
        super().__init__(**kwargs)
        self.running = True
        self.images = images
        self.photo_type_spec = photo_type_spec
        self.photo_data = [{} for i in range(len(self.images))]
        self.active_photo = None
        self.photo_index = 0
        self.show_photo()


    def show_photo(self):
        if self.active_photo:
            self.active_photo.die(None)
            self.active_photo = None
        self.active_photo = self.photo_type_spec.create(image_asset = self.images[self.photo_index])
        self.active_photo.transform()


    def update(self, delta):
        """Updates the game."""
        super().update(delta)
        self.handle_input()


    def direct_draw(self):
        try:
            # Show dot in focal point if there is one
            focal_point = self.photo_data[self.photo_index]["focal_point"]
            world_pos = self.normalized_to_world(focal_point, self.active_photo.rect)
            pygame.draw.circle(self.screen, pygame.Color(240, 250, 70), world_pos, 0.01 * self.screen.get_rect().width)

        except KeyError as e:
            pass


    def handle_input(self):
        """Reads input and makes things happen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_RIGHT:
                    if self.photo_index < len(self.images) - 1:
                        self.photo_index += 1
                        self.show_photo()
                if event.key == pygame.K_LEFT:
                    if self.photo_index > 0:
                        self.photo_index -= 1
                        self.show_photo()
                if event.key == pygame.K_o:
                    print(self.photo_data)

            if event.type == pygame.MOUSEBUTTONUP:
                if self.active_photo.rect.collidepoint(pygame.mouse.get_pos()):
                    focal_point = self.world_to_normalized(pygame.mouse.get_pos(), self.active_photo.rect)
                    self.photo_data[self.photo_index]["focal_point"] = focal_point

    def world_to_normalized(self, world_pos: pygame.Vector2, rect: pygame.Rect) -> pygame.Vector2:
        local_pos = world_pos - pygame.Vector2(rect.topleft)
        normalized_pos = pygame.Vector2(local_pos.x / rect.width, local_pos.y / rect.height)
        return normalized_pos

    def normalized_to_world(self, normalized_pos: pygame.Vector2, rect: pygame.Rect) -> pygame.Vector2:
        local_pos = pygame.Vector2(normalized_pos.x * rect.width, normalized_pos.y * rect.height)
        world_pos = rect.topleft + local_pos
        return world_pos