#!/usr/bin/env python3
import os
import numpy as np
import pygame
import sys
import time
import random
import pickle

from enum import Enum, auto

from pygame.locals import *

FPS = 30
HEX_RADIUS = 100
BG_LINE_WIDTH = 3

def hexToSquare(u, v):
    x = ((u - v) * (3 * HEX_RADIUS) / 2.0)
    y = -((u + v) * (HEX_RADIUS / (2.0 * np.tan(np.pi / 6))))
    return (x, y)

def squareToHex(x, y):
    u = np.round(((x / 3.0) - y * np.tan(np.pi / 6)) / HEX_RADIUS)
    v = - np.round(((x / 3.0) + y * np.tan(np.pi / 6)) / HEX_RADIUS)
    return (u, v)

class Game(object):
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.key.set_repeat(1, 180)
        self._clock = pygame.time.Clock()

        self._fpsClock = pygame.time.Clock()
        #self._screen = pygame.display.set_mode((800, 600))
        self._screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self._surface = pygame.Surface(self._screen.get_size())
        self._surface = self._surface.convert()
        self._clear()
        self._screen.blit(self._surface, (0,0))

        self._drag_loc = None
        self.center = (0, 0)
        self._font = pygame.font.SysFont('Comic Sans MS', 30)
        self.zoom = 1.0
        self.tiles = {}
        self._selected_tile = None
        self._selected_slices = []
        self._select_text = ""
        self._expanded_slice = None
        self._expand_center = None

    def _clear(self):
        self._surface.fill((0, 25, 30))

    def _flip(self):
        self._screen.blit(self._surface, (0, 0))
        pygame.display.flip()
        pygame.display.update()

    def _pointHex(self):
        screen_size = self._screen.get_size()
        point = pygame.mouse.get_pos()
        point = tuple(np.subtract(point, np.divide(screen_size, 2)))
        point = tuple(np.divide(point, self.zoom))
        point = tuple(np.subtract(self.center, point))
        return squareToHex(*point)

    def _pointSlice(self):
        screen_size = self._screen.get_size()
        point = pygame.mouse.get_pos()
        point = tuple(np.subtract(point, np.divide(screen_size, 2)))
        point = tuple(np.divide(point, self.zoom))
        point = tuple(np.subtract(self.center, point))
        hex_idx = squareToHex(*point)
        hex_center = hexToSquare(*hex_idx)
        ang = (np.round((np.arctan2(hex_center[1] - point[1], hex_center[0] - point[0]) - (np.pi / 6)) / (np.pi / 3)) + 6) % 6
        return hex_idx, int(ang)


    def _checkEvent(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if self._selected_tile and self._selected_tile.type == Tile.Type.UNKNOWN:
                        self._selected_tile = None
                    if self._selected_slices and not self._selected_slices[0].type:
                        self._selected_slices = []
                    if self._expanded_slice:
                        tile_id, ang, slices = self._expanded_slice
                        self.tiles[tile_id].slices[ang] = slices
                        self._expanded_slice = None
                # Tile select mode.
                if ((self._selected_tile and self._selected_tile.type == Tile.Type.UNKNOWN) or
                    (self._selected_slices and not self._selected_slices[0].type)):
                    if event.key == K_BACKSPACE:
                        self._select_text =  self._select_text[:-1]
                    elif event.key == K_DELETE:
                        self._select_text = ""
                    elif event.key == K_RETURN:
                        if self._selected_tile:
                            valid_names = [i.name for i in Tile.Type if self._select_text.upper() in i.name]
                            if valid_names:
                                self._selected_tile.type = Tile.Type[valid_names[0]]
                        elif self._selected_slices:
                            valid_names = [i for i in Slice.types if self._select_text.upper() in i]
                            if valid_names:
                                for s in self._selected_slices:
                                    s.type = valid_names[0]
                    elif self._selected_slices and not (self._select_text and self._select_text[-1] == "_") and event.unicode.isnumeric():
                        num = int(event.unicode)
                        if self._selected_slices and 0 < num <= 5:
                            self._selected_slices = []
                            for _ in range(num):
                                self._selected_slices.append(Slice())
                    else:
                        self._select_text += event.unicode
                else:
                    if event.key == K_q:
                        with open("./game_state", "+wb") as f:
                            pickle.dump(self.tiles, f)
                        pygame.quit()
                        sys.exit()
                    elif event.key == K_t:
                        if not self._selected_tile and not self._selected_slices:
                            self._selected_tile = Tile()
                    elif event.key == K_s:
                        if not self._selected_slices and not self._selected_tile:
                            self._selected_slices.append(Slice())
                    elif event.key == K_d:
                        if self._selected_slices:
                            self._selected_slices = []
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    curr_tile, ang = self._pointSlice()
                    if self._expand_center and self._expanded_slice and len(self._selected_slices) < 5:
                        mouse_pos = pygame.mouse.get_pos()
                        if np.fabs(mouse_pos[0] - self._expand_center[0]) < HEX_RADIUS / 3 * self.zoom:
                            selected = -1
                            for i, s in enumerate(self._expanded_slice[2]):
                                if np.fabs(mouse_pos[1] - self._expand_center[1] + (i + 0.5) * self.zoom * HEX_RADIUS/2) < HEX_RADIUS / 3 * self.zoom:
                                    self._selected_slices.insert(0, s)
                                    selected = i
                                    break
                            if selected > -1:
                                del(self._expanded_slice[2][selected])
                                if not self._expanded_slice[2]:
                                    self._expanded_slice = None
                                    self._expand_center = None
                                continue

                    if self._selected_tile or self._selected_slices:
                        if curr_tile not in self.tiles and self._selected_tile and self._selected_tile.type != Tile.Type.UNKNOWN:
                            self._selected_tile.set()
                            self.tiles[curr_tile] = self._selected_tile
                            self._selected_tile = None
                        elif curr_tile in self.tiles and self._selected_slices and self._selected_slices[0].type:
                            ang -= self.tiles[curr_tile].rotation
                            ang = (ang + 6) % 6
                            if len(self.tiles[curr_tile].slices[ang]) <= 5 - len(self._selected_slices) and (not self._expanded_slice or curr_tile != self._expanded_slice[0] or ang != self._expanded_slice[1]):
                                self.tiles[curr_tile].slices[ang] += self._selected_slices
                                self._selected_slices = []
                    else:
                        if curr_tile in self.tiles:
                            ang -= self.tiles[curr_tile].rotation
                            ang = (ang + 6) % 6
                            if not self._selected_tile and pygame.key.get_pressed()[K_LSHIFT]:
                                self._selected_tile = self.tiles[curr_tile]
                                del(self.tiles[curr_tile])
                            elif not self._selected_slices and (not self._expanded_slice or (self._expanded_slice[0] != curr_tile or self._expanded_slice[1] != ang)):
                                if self.tiles[curr_tile].slices[ang]:
                                    self._selected_slices = self.tiles[curr_tile].slices[ang]
                                    self.tiles[curr_tile].slices[ang] = []
                elif event.button == 2: # middle button
                    self._drag_loc = pygame.mouse.get_pos()
                elif event.button == 3: # right button
                    curr_tile, ang = self._pointSlice()
                    if curr_tile in self.tiles and pygame.key.get_pressed()[K_LSHIFT]:
                        self.tiles[curr_tile].rotation += 1
                    elif not self._selected_slices:
                        if curr_tile in self.tiles:
                            ang -= self.tiles[curr_tile].rotation
                            ang = (ang + 6) % 6
                            if not self._selected_tile and pygame.key.get_pressed()[K_LSHIFT]:
                                self._selected_tile = self.tiles[curr_tile]
                                del(self.tiles[curr_tile])
                            elif not self._expanded_slice:
                                if self.tiles[curr_tile].slices[ang]:
                                    self._expanded_slice = (curr_tile, ang, self.tiles[curr_tile].slices[ang])
                                    self.tiles[curr_tile].slices[ang] = []
                            elif self._expanded_slice:
                                if curr_tile == self._expanded_slice[0] and ang == self._expanded_slice[1]:
                                    self.tiles[curr_tile].slices[ang] = self._expanded_slice[2]
                                    self._expanded_slice = None
                                else:
                                    self.tiles[self._expanded_slice[0]].slices[self._expanded_slice[1]] = self._expanded_slice[2]
                                    self._expanded_slice = None
                                    self._expanded_slice = (curr_tile, ang, self.tiles[curr_tile].slices[ang])
                                    self.tiles[curr_tile].slices[ang] = []
                    elif self._selected_slices:
                        if curr_tile in self.tiles:
                            ang -= self.tiles[curr_tile].rotation
                            ang = (ang + 6) % 6
                            if self._expanded_slice and self._expanded_slice[0] == curr_tile and self._expanded_slice[1] == ang:
                                tile_id, ang, slices = self._expanded_slice
                                self.tiles[tile_id].slices[ang] = slices
                                self._expanded_slice = None
                            elif len(self.tiles[curr_tile].slices[ang]) < 5:
                                self.tiles[curr_tile].slices[ang].append(self._selected_slices[0])
                                del(self._selected_slices[0])



                elif event.button == 4: # scroll up?
                    if self.zoom < 1.5:
                        self.zoom /= 0.96
                elif event.button == 5: # scroll down?
                    if self.zoom > 0.2:
                        self.zoom *= 0.96
            elif event.type == pygame.MOUSEMOTION:
                if self._drag_loc:
                    cur_pos = pygame.mouse.get_pos()
                    self.center = tuple(np.add(
                        self.center,
                        np.subtract(cur_pos,
                            self._drag_loc) / self.zoom))
                    self._drag_loc = cur_pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self._drag_loc = None

    def step(self):
        self._checkEvent()
        self._clear()
        self._draw()
        self._flip()
        self._fpsClock.tick(FPS)

    def _draw(self):
        screen_size = self._screen.get_size()
        center_tile = squareToHex(*self.center)
        shifted_center = hexToSquare(*center_tile)
        offset = tuple(np.subtract(self.center, shifted_center) * self.zoom)
        num_tiles = int(np.ceil(screen_size[0] / (HEX_RADIUS * self.zoom) / 3)) + 1

        tiles_to_draw = []
        tile_y = []
        for u in list(range(-num_tiles, num_tiles)):
            for v in list(range(-num_tiles, num_tiles)):
                tile_center = hexToSquare(u, v)
                tile_id = (center_tile[0] - u, center_tile[1] - v)
                tile_center = tuple(np.multiply(tile_center, self.zoom))
                tile_center = tuple(np.add(tile_center, offset))
                tile_center = tuple(np.add(tile_center, np.divide(screen_size, 2)))
                if tile_center[0] < -HEX_RADIUS * self.zoom:
                    continue
                if tile_center[0] > screen_size[0] + (HEX_RADIUS * self.zoom):
                    continue
                if tile_center[1] < -HEX_RADIUS * self.zoom:
                    continue
                if tile_center[1] > screen_size[1] + (HEX_RADIUS * self.zoom):
                    continue
                angles = [i * (np.pi / 3.0) for i in range(4)]
                pnts_x = HEX_RADIUS * self.zoom * np.cos(angles) + tile_center[0]
                pnts_y = HEX_RADIUS * self.zoom * np.sin(angles) + tile_center[1]
                pygame.draw.lines(self._surface, (170, 195, 200), False,
                                  list(zip(pnts_x, pnts_y)), BG_LINE_WIDTH)
                if tile_id in self.tiles:
                    tile = tile_id
                    tile_y.append(tile_center[1])
                    tiles_to_draw.append((tile, (self._surface, tile_center, self.zoom)))
        y_ord = np.argsort(tile_y)
        for tile_id, args in tiles_to_draw:
            self.tiles[tile_id].draw(*args)
        for i in y_ord:
            (tile_id, args) = tiles_to_draw[i]
            self.tiles[tile_id].draw_slices(*args)
        self._expand_center = None
        slice_to_draw = []
        for tile_id, args in tiles_to_draw:
            if self._expanded_slice and self._expanded_slice[0] == tile_id:
                tile_pos, ang, slices = self._expanded_slice
                center = args[1]
                real_ang = ang + self.tiles[tile_pos].rotation
                trig_x = (HEX_RADIUS * self.zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.cos(real_ang * np.pi/3 + np.pi / 6) + center[0]
                trig_y = (HEX_RADIUS * self.zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.sin(real_ang * np.pi/3 + np.pi / 6) + center[1]
                self._expand_center = (trig_x, trig_y)
                for idx, i in enumerate(slices):
                    slice_to_draw.append((i, (self._surface, (trig_x, trig_y - (idx + 0.5) * self.zoom * HEX_RADIUS/2 ) , real_ang * np.pi/3  , self.zoom, (len(slices) - 1) - idx)))
        for i, args in slice_to_draw:
            i.draw(*args)
        if self._selected_slices or self._selected_tile:
            mouse_pos = pygame.mouse.get_pos()
            if self._selected_slices:
                for idx, i in enumerate(self._selected_slices):
                    i.draw(self._surface, (mouse_pos[0], mouse_pos[1] - idx * self.zoom * HEX_RADIUS/2 ) , np.pi/3, self.zoom, (len(self._selected_slices) - 1) - idx)
            elif self._selected_tile:
                self._selected_tile.draw(self._surface, pygame.mouse.get_pos(), self.zoom)
            if ((self._selected_tile and self._selected_tile.type == Tile.Type.UNKNOWN) or
                (self._selected_slices and not self._selected_slices[0].type)):
                text = self._font.render("> " + self._select_text, False, (255, 255, 255))
                text_rect = text.get_rect()
                text_rect.center = pygame.mouse.get_pos()
                text_box = pygame.Rect.copy(text_rect)
                text_box.height += 3
                text_box.width = 200
                text_box.center = pygame.mouse.get_pos()
                pygame.draw.rect(self._surface, (0, 0, 0), text_box, 0)
                self._surface.blit(text, text_rect)
                if self._selected_slices:
                    valid_names = [i for i in Slice.types if self._select_text.upper() in i]
                elif self._selected_tile:
                    valid_names = [i.name for i in Tile.Type if self._select_text.upper() in i.name]
                for idx, t in enumerate(valid_names):
                    text = self._font.render(t, False, (255, 255, 255))
                    text_rect = text.get_rect()
                    text_box = pygame.Rect.copy(text_rect)
                    text_box.height += 3
                    text_box.width = 180
                    center = pygame.mouse.get_pos()
                    center =(center[0], center[1] + text_box.height * (idx + 1))
                    text_box.center = center
                    text_rect.center = center
                    pygame.draw.rect(self._surface, (10, 10, 10), text_box, 0)
                    self._surface.blit(text, text_rect)



class Slice(object):
    types = []
    images = {}
    def __init__(self):
        if not self.types:
            for f in os.listdir("./slice_images/"):
                if f.endswith(".png"):
                    self.types.append(f[:-4].upper())
        self.type = ""

    def draw(self, surface, slice_center, rotation, zoom, depth, draw_img=True):
        trig_angles = np.array([i * (np.pi / 3 * 2) + rotation + np.pi / 2 for i in range(3)])
        trig_length = (HEX_RADIUS * zoom * 0.51 - BG_LINE_WIDTH * 2)
        trig_pnts_x = trig_length * np.cos(trig_angles) + slice_center[0]
        trig_pnts_y = trig_length * np.sin(trig_angles) + slice_center[1]

        pygame.draw.polygon(surface, (210 - 20  * depth, 210 - 20 * depth, 210 - 20 * depth),
                          list(zip(trig_pnts_x, trig_pnts_y)), 0)
        if self.type and draw_img:
            name = "./slice_images/%s.png" % self.type.lower()
            if name not in self.images:
                if os.path.isfile(name):
                    self.images[name] = pygame.image.load("./slice_images/%s.png" % self.type.lower())
            
            if name in self.images:
                img_surf = self.images[name]
                img_length = int(np.round(trig_length * np.sin(np.pi / 6) * 2))
                img_surf = pygame.transform.scale(img_surf, (img_length, img_length))
                img_rect = img_surf.get_rect()
                img_rect.center = slice_center
                surface.blit(img_surf, img_rect)



class Tile(object):
    class Type(Enum):
        FOREST = auto()
        CROP = auto()
        DUNGEON = auto()
        R_FOREST = auto()
        R_CROP = auto()
        R_DUNGEON = auto()
        PLAYER_1_INVENTORY = auto()
        PLAYER_2_INVENTORY = auto()
        UNKNOWN = auto()

    def __init__(self):
        self.rotation = 0
        self.type = Tile.Type.UNKNOWN
        self.slices = [[] for _ in range(6)]

    def set(self):
        if self.type.name.startswith("R_"):
            selection = [Tile.Type.FOREST, Tile.Type.CROP, Tile.Type.DUNGEON] + [Tile.Type[self.type.name[2:]]] * 3
            self.type = selection[np.random.randint(len(selection))]
            if self.type == Tile.Type.FOREST:
                probs = [
                        [""] * 10 + ["bat"] * 5 + ["gold"] + ["tree"] * 50 + ["water"] * 20 + ["stone"] * 7
                        ] * 6
            elif self.type == Tile.Type.CROP:
                probs = [
                        [""] * 10 + ["wheat"] * 25 + ["tree"] * 5 + ["wagon"] * 5 + ["water"] * 20 + ["chicken"] * 10 + ["egg"] * 2 + ["axe"] * 7 + ["stone"] * 2
                        ] * 6
            elif self.type == Tile.Type.DUNGEON:
                probs = [
                        [""] * 7 + ["bat"] * 20 + ["gold"] * 5 + ["dagger"] * 5 + ["gem"] * 5 + ["dragon"] * 2 + ["torch"] * 5 + ["spider"] * 10 + ["stone"] * 10
                        ] * 6
            for idx, s in enumerate(probs):
                type_name = s[np.random.randint(len(s))]
                if type_name:
                    new_slice = Slice()
                    new_slice.type = type_name
                    self.slices[idx].append(new_slice)

                                

    def draw(self, surface, tile_center, zoom):
        colour = (128, 128, 128)
        if self.type == Tile.Type.FOREST:
            colour = (10, 100, 10)
        elif self.type == Tile.Type.CROP:
            colour = (175, 175, 0)
        elif self.type == Tile.Type.DUNGEON:
            colour = (65, 65, 65)
        elif self.type == Tile.Type.R_FOREST:
            colour = (50, 100, 50)
        elif self.type == Tile.Type.R_CROP:
            colour = (175, 175, 50)
        elif self.type == Tile.Type.R_DUNGEON:
            colour = (85, 85, 85)
        elif self.type == Tile.Type.PLAYER_1_INVENTORY:
            colour = (200, 10, 10)
        elif self.type == Tile.Type.PLAYER_2_INVENTORY:
            colour = (10, 10, 200)
        angles = np.array([(i + self.rotation) * (np.pi / 3.0) for i in range(6)])
        trig_x = (HEX_RADIUS * zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.cos(angles + np.pi / 6) + tile_center[0]
        trig_y = (HEX_RADIUS * zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.sin(angles + np.pi / 6) + tile_center[1]
        sorted_idx = np.argsort(trig_y)
        for i in sorted_idx:
            trig_rot = angles[i]
            center = (trig_x[i], trig_y[i])
            trig_angles = np.array([j * (np.pi / 3 * 2) + trig_rot + np.pi / 2 for j in range(3)])
            trig_pnts_x = HEX_RADIUS * zoom * 0.51 * np.cos(trig_angles) + center[0]
            trig_pnts_y = HEX_RADIUS * zoom * 0.51 * np.sin(trig_angles) + center[1]
            pygame.draw.polygon(surface, colour,
                              list(zip(trig_pnts_x, trig_pnts_y)), BG_LINE_WIDTH)

    def draw_slices(self, surface, tile_center, zoom):
        angles = np.array([(i + self.rotation) * (np.pi / 3.0) for i in range(6)])
        trig_x = (HEX_RADIUS * zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.cos(angles + np.pi / 6) + tile_center[0]
        trig_y = (HEX_RADIUS * zoom - BG_LINE_WIDTH) * np.tan(np.pi / 6) * np.sin(angles + np.pi / 6) + tile_center[1]
        sorted_idx = np.argsort(trig_y)
        for i in sorted_idx:
            center = (trig_x[i], trig_y[i])
            trig_rot = angles[i]
            if self.slices[i]:
                for idx, j in enumerate(self.slices[i]):
                    j.draw(surface, (center[0], center[1] - idx * zoom * 5), trig_rot, zoom, len(self.slices[i]) - 1 - idx, idx == len(self.slices[i]) - 1)



def main():
    np.random.seed()
    game = Game()
    if os.path.isfile("./game_state"):
        with open("./game_state", "rb") as f:
            game.tiles = pickle.load(f)
    while True:
        game.step()

if __name__ == '__main__':
    main()
