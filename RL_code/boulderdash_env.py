import gymnasium
from gymnasium import spaces

import numpy as np
import copy

import pygame
from pygame.locals import *

from collections import deque

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from BoulderDash import readLevelsFile, makeMove, rockHasToFall, isLevelFinished

class BoulderDashEnv(gymnasium.Env):
    metadata = {"render_modes": ["human"]}
    TILE_SIZE = 20  # size of each tile in pixels for rendering
    

    def __init__(self, level_file='BoulderLevels.txt', level_index=0, render_mode=None, render_speed=2000):
        super().__init__()
        self.render_mode = render_mode
        self.render_speed = render_speed
        
        self.init_lvl_index = level_index
        self.level_index = level_index
        self.levels = readLevelsFile(level_file)  # store all levels
        self.levelObj = self.levels[self.level_index]
        self.mapObj = copy.deepcopy(self.levelObj['mapObj'])
        self.gameStateObj = copy.deepcopy(self.levelObj['startState'])

        # Action space: stay/up/down/left/right
        self.action_space = spaces.Discrete(5)

        # Observation space: grid of integers
        self.width = self.levelObj['width']
        self.height = self.levelObj['height']
        self.visited = np.zeros((self.width, self.height), dtype=np.float32)
        self.steps = None
        self.steps_since_gem = None
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(8,), dtype=np.float32)
        self.dead = False
        self.level_complete = False
        self.prev_gem_count = None
        self.current_dist_to_gem = None
        self.prev_dist_to_gem = None
        self.nearest_gem_pos = None
        self.next_action = None
        self.same_pos_count = None
        self.prev_pos = None

        self.lvl_count = 0

        # Pygame rendering setup
        self.screen = None
        self.clock = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.level_index = self.init_lvl_index
        self.levelObj = self.levels[self.level_index]
        self.mapObj = copy.deepcopy(self.levelObj['mapObj'])
        self.gameStateObj = copy.deepcopy(self.levelObj['startState'])
        self.dead = False
        self.level_complete = False

        #custom
        self.visited = np.zeros((self.width, self.height), dtype=np.float32)
        self.steps = 0
        self.steps_since_gem = 0
        self.prev_gem_count = 0
        self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond({'=', '#', 'o'})
        self.prev_dist_to_gem = self.current_dist_to_gem
        self.next_action = 0
        self.same_pos_count = 0
        self.prev_pos = (0, 0)

        return self._get_obs(), {}

    def step(self, action):
        action = int(action)
        self.next_action = action
        action_map = {0: 'up', 1: 'left', 2: 'down', 3: 'right', 4: None}
        move = action_map[action]
        
        if move is not None:
            self.moved = makeMove(self.mapObj, self.gameStateObj, move)
        fell, self.dead = rockHasToFall(self.mapObj, self.gameStateObj)
        self.level_complete = isLevelFinished(self.levelObj, self.gameStateObj)
        reward, termination, truncated = self._compute_reward()
        obs = self._get_obs()
        self.prev_pos = self.gameStateObj['player']

        if self.render_mode == "human":
            self.render()

        return obs, reward, termination, truncated, {}

    def _compute_target_reachable(self, searching_for_diamond):
        reachable = np.zeros((self.width, self.height), dtype=bool)
        queue = deque()

        if searching_for_diamond:
            for x, y, _ in self.gameStateObj['diamonds']:
                reachable[x][y] = True
                queue.append((x, y))
        else:
            dx, dy = self.gameStateObj['door']
            reachable[dx][dy] = True
            queue.append((dx, dy))

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if reachable[nx][ny]:
                    continue

                tile = self.mapObj[nx][ny]
                if tile in {'#', '=', 'o'}:
                    continue

                reachable[nx][ny] = True
                queue.append((nx, ny))

        return reachable

    def _bfs_distance_to_nearest_diamond(self, blocked):
        px, py = self.gameStateObj['player']

        diamonds = {(x, y) for x, y, _ in self.gameStateObj['diamonds']}
        searching_for_diamond = len(diamonds) > 0
        door = self.gameStateObj['door']

        # reachable space
        visited = set()
        queue = deque([(px, py, 0)])
        parents = {(px, py): None}
        visited.add((px, py))

        while queue:
            x, y, dist = queue.popleft()

            # Target reached normally
            if searching_for_diamond:
                if (x, y) in diamonds:
                    step_x, step_y = x, y
                    while parents[(step_x, step_y)] not in [(px, py), None]:
                        step_x, step_y = parents[(step_x, step_y)]
                    return dist, (step_x, step_y)
            else:
                if (x, y) == door:
                    step_x, step_y = x, y
                    while parents[(step_x, step_y)] not in [(px, py), None]:
                        step_x, step_y = parents[(step_x, step_y)]
                    return dist, (step_x, step_y)

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if (nx, ny) in visited:
                    continue
                if self.mapObj[nx][ny] in blocked:
                    continue

                visited.add((nx, ny))
                parents[(nx, ny)] = (x, y)
                queue.append((nx, ny, dist + 1))

        # toward useful rocks
        target_reachable = self._compute_target_reachable(searching_for_diamond)

        best_dist = 999
        best_tile = None

        for x, y in visited:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                rx, ry = x + dx, y + dy
                if not (0 <= rx < self.width and 0 <= ry < self.height):
                    continue
                if self.mapObj[rx][ry] != 'o':
                    continue

                bx, by = rx + dx, ry + dy
                if not (0 <= bx < self.width and 0 <= by < self.height):
                    continue

                if target_reachable[bx][by]:
                    dist = abs(px - x) + abs(py - y)
                    if dist < best_dist:
                        best_dist = dist
                        best_tile = (x, y)

        # Backtrack first step
        if best_tile is not None:
            step_x, step_y = best_tile
            while parents[(step_x, step_y)] not in [(px, py), None]:
                step_x, step_y = parents[(step_x, step_y)]
            return best_dist, (step_x, step_y)

        return 999, (px, py)


    def _get_obs(self):
        px, py = self.gameStateObj['player']

        self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond({'=', '#', 'o'})

        def rock_obs(x_offset):
            if self.mapObj[px+x_offset][py-2] == "o":
                if self.mapObj[px+x_offset][py-1] == "s":
                    return 1.0
            elif self.mapObj[px+x_offset][py-1] == "o" and self.mapObj[px+x_offset][py] == "s":
                return 1.0
            return 0.0
        
        left_above = rock_obs(-1)
        center_above = rock_obs(0)
        right_above = rock_obs(1)
        
        obs = np.array([
            px / self.width, 
            py / self.height, 
            (self.nearest_gem_pos[0]-px+1)/2.0, 
            (self.nearest_gem_pos[1]-py+1)/2.0,
            self.current_dist_to_gem / 46.0, 
            left_above,
            center_above,
            right_above,
        ], dtype=np.float32)

        return obs

    def _load_level(self, index):
        self.levelObj = self.levels[index]
        self.mapObj = copy.deepcopy(self.levelObj['mapObj'])
        self.gameStateObj = copy.deepcopy(self.levelObj['startState'])
        self.width = self.levelObj['width']
        self.height = self.levelObj['height']

    def _compute_reward(self):
        px, py = self.gameStateObj['player']
        self.steps += 1
        self.steps_since_gem += 1
        terminated = False
        truncated = False

        still_punishment = 0
        if self.prev_pos == (px, py):
            self.same_pos_count += 1
            if self.same_pos_count > 5:
                still_punishment = 2.0
        else:
            self.same_pos_count = 0

        #collect gem reward
        gem_reward = 0
        if self.prev_gem_count < len(self.levelObj['startState']['diamonds']) - len(self.gameStateObj['diamonds']):
            gem_reward = 2.0
            self.prev_gem_count = len(self.levelObj['startState']['diamonds']) - len(self.gameStateObj['diamonds'])
            self.steps_since_gem = 0
        
        if self.steps >= 1000: #timeout punishment
            reward = -2
            truncated = True
        elif self.dead: #death punishment
            reward = -2.0
            terminated = True
        elif len(self.gameStateObj['diamonds']) == 0 and (px, py) == self.gameStateObj['door']: #goal
            reward = 10.0
            self.lvl_count += 1
            if self.lvl_count == 5:
                self.init_lvl_index += 1
                self.lvl_count = 0
            terminated = True
        else: #delta distance to gem reward
            reward = ((self.prev_dist_to_gem - self.current_dist_to_gem)*0.2 + gem_reward - still_punishment)
            self.prev_dist_to_gem = self.current_dist_to_gem

        return reward, terminated, truncated

    def render(self):
        if self.render_mode != "human":
            return

        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode(
                (self.width * self.TILE_SIZE, self.height * self.TILE_SIZE)
            )
            pygame.display.set_caption("Boulder Dash")
            self.clock = pygame.time.Clock()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.screen.fill((0, 0, 0))

        colors = {
            "s": (0, 0, 0),       # empty
            "#": (128, 128, 128), # border
            "=": (128, 128, 128), # wall
            "o": (255, 165, 0),   # rock
            "d": (0, 255, 255),   # diamond
            "e": (0, 255, 0),     # exit
            "@": (255, 0, 0),     # player
            "x": (74, 54, 54),    # dirt
        }

        # Draw map tiles
        for x in range(self.width):
            for y in range(self.height):
                tile = self.mapObj[x][y]
                color = colors.get(tile, (0, 0, 0))

                rect = pygame.Rect(
                    x * self.TILE_SIZE,
                    y * self.TILE_SIZE,
                    self.TILE_SIZE,
                    self.TILE_SIZE
                )
                pygame.draw.rect(self.screen, color, rect)

        # Draw player
        px, py = self.gameStateObj['player']
        pygame.draw.rect(
            self.screen,
            (255, 0, 0),
            pygame.Rect(
                px * self.TILE_SIZE,
                py * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE
            )
        )

        pygame.display.flip()
        self.clock.tick(self.render_speed)

    def close(self):
        if self.screen:
            pygame.quit()
            self.screen = None
            self.clock = None
    
