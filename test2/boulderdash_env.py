import gymnasium
from gymnasium import spaces

import numpy as np
import copy

import pygame
from pygame.locals import *

from collections import deque
import random

import sys
sys.path.append("C://Users//Ludwig//OneDrive - KTH//ÅK3//P2//id1214//boulder-dash-main//boulder-dash-main")

from BoulderDash import readLevelsFile, makeMove, moveEnemies, rockHasToFall, isLevelFinished

class BoulderDashEnv(gymnasium.Env):
    metadata = {"render_modes": ["human"]}
    TILE_SIZE = 20  # size of each tile in pixels for rendering

    def __init__(self, level_file='BoulderLevels.txt', level_index=0, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        
        self.init_lvl_index = level_index
        self.level_index = level_index
        self.levels = readLevelsFile(level_file)  # store all levels
        self.levelObj = self.levels[self.level_index]
        #self.levelObj = readLevelsFile(level_file)[level_index]
        self.mapObj = copy.deepcopy(self.levelObj['mapObj'])
        self.gameStateObj = copy.deepcopy(self.levelObj['startState'])

        # Action space: stay/up/down/left/right
        self.action_space = spaces.Discrete(4)

        # Observation space: grid of integers
        self.width = self.levelObj['width']
        self.height = self.levelObj['height']
        self.visited = [0,0,0,0,0,0,0,0,0,0]
        self.centerPos = []
        self.steps = None
        self.steps_since_gem = None
        self.prev_actions = []
        self.observation_space = spaces.Box(low=0, high=40, shape=(12,), dtype=np.float32)
        self.dead = False
        self.level_complete = False
        self.prev_gem_count = None
        self.current_dist_to_gem = None
        self.prev_dist_to_gem = None
        self.nearest_gem_pos = None
        self.blockedStone = {'#', '=', 'o'}
        self.blockedNostone = {'#', '='}
        self.currentAction = None
        self.lastPosCounter = None


        # Pygame rendering setup
        self.screen = None
        self.clock = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        #self.level_index = self.init_lvl_index
        self.level_index = random.randrange(0, 7)
        self.levelObj = self.levels[self.level_index]
        self.mapObj = copy.deepcopy(self.levelObj['mapObj'])
        self.gameStateObj = copy.deepcopy(self.levelObj['startState'])
        self.dead = False
        self.level_complete = False

        #custom
        self.visited = [0,0,0,0,0,0,0,0,0,0]
        self.centerPos = [0,0]
        self.lastPosCounter = 0
        self.currentAction = 0
        self.steps = 0
        self.steps_since_gem = 0
        self.prev_actions = [0,1,2,3,0]
        self.prev_gem_count = 0
        self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond(self.blockedStone)
        self.prev_dist_to_gem = self.current_dist_to_gem
        

        return self._get_obs(), {}

    def step(self, action):
        action = int(action)
        self.prev_actions.append(action)
        action_map = {0: 'up', 1: 'left', 2: 'down', 3: 'right'}
        move = action_map[action]
        self.currentAction = action
        
        if move is not None:
            self.moved = makeMove(self.mapObj, self.gameStateObj, move)
        fell, self.dead = rockHasToFall(self.mapObj, self.gameStateObj)
        self.level_complete = isLevelFinished(self.levelObj, self.gameStateObj)
        reward, termination = self._compute_reward()
        obs = self._get_obs()
        truncated = False

        if self.render_mode == "human":
            self.render()

        return obs, reward, termination, truncated, {}

    def _bfs_distance_to_nearest_diamond(self, blocked):
        px, py = self.gameStateObj['player']
        diamonds = set(self.gameStateObj['diamonds'])

        visited = set()
        queue = deque()
        queue.append((px, py, 0))
        visited.add((px, py))

        blocked = blocked  # walls
        for i in range(2):
            searching_for_diamond = len(diamonds) > 0

            # Track parent to find the first step
            parents = {(px, py): None}

            while queue:
                x, y, dist = queue.popleft()

                # Found target
                if searching_for_diamond:
                    if (x, y) in diamonds:
                        # backtrack to find first move
                        step_x, step_y = x, y
                        while parents[(step_x, step_y)] not in [(px, py), None]:
                            step_x, step_y = parents[(step_x, step_y)]
                        return dist, (step_x, step_y)
                else:
                    if (x, y) == self.gameStateObj['door']:
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
                    tile = self.mapObj[nx][ny]
                    if tile in blocked:
                        continue

                    visited.add((nx, ny))
                    parents[(nx, ny)] = (x, y)
                    queue.append((nx, ny, dist + 1))

            # No reachable target, return player position
            #return 999, (px, py)
            visited = set()
            queue = deque()
        return 999, (px, py) 

    def _get_obs(self):
        
        px, py = self.gameStateObj['player']

        diamonds = self.gameStateObj['diamonds']
        self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond(self.blockedStone)
        if(self.current_dist_to_gem == 999):
            self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond(self.blockedNostone)
        #print((self.nearest_gem_pos[0]-px, self.nearest_gem_pos[1]-py))
        
        #gems_collected = len(self.levelObj['startState']['diamonds']) - len(self.gameStateObj['diamonds'])
        """local = []
        for dx in [-1,0,1]:
            for dy in [-2,-1,0]:
                x, y = px + dx, py + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.mapObj[x][y] == 'o':
                        local.append(0.6)
                    elif self.mapObj[x][y] == 'd':
                        local.append(0.3)
                    elif self.mapObj[x][y] == 'x':
                        local.append(0.1)
                    elif self.mapObj[x][y] == '=' or self.mapObj[x][y] == '#':
                        local.append(1.0)
                    else:
                        local.append(0.0)
                    #local.append(
                    #    1 if self.mapObj[x][y] == 'o' else 0
                    #)
                else:
                    local.append(1.0)  """
        
        if(len(self.prev_actions) > 5):
            self.prev_actions.pop(0)

        self.visited.extend([px,py])

        if(len(self.visited) > 10):
            self.visited.pop(0)
            self.visited.pop(0)

        central_above = 0
        left_above = 0
        right_above = 0
        right = 0
        left = 0

        if(self.mapObj[px] and self.mapObj[py-1] == 's' and self.mapObj[px] and self.mapObj[py-2] == 'o' ):
            central_above = 1
        if(self.mapObj[px-1] and self.mapObj[py-1] == 's' and self.mapObj[px-1] and self.mapObj[py-2] == 'o' ):
            left_above = 1
        if(self.mapObj[px+1] and self.mapObj[py-1] == 's' and self.mapObj[px+1] and self.mapObj[py-2] == 'o' ):
            right_above = 1
        if(self.mapObj[px+1] and self.mapObj[py] == 'o' and self.mapObj[px+2] and self.mapObj[py] == 's'):
            right = 1
        if(self.mapObj[px-1] and self.mapObj[py] == 'o' and self.mapObj[px-2] and self.mapObj[py] == 's'):
            left = 1
        
        #obs = np.array([px, py, closest_dx, closest_dy, gems_collected]) # + list(self.prev_actions)
        obs = np.array([
            px, py, 
            self.nearest_gem_pos[0]-px, 
            self.nearest_gem_pos[1]-py,
            self.current_dist_to_gem, 
            #*self.prev_actions,
            #*self.visited,
            #*local
            central_above,
            left_above,
            right_above,
            right,
            left,
            self.centerPos[0],
            self.centerPos[1]

        ], dtype=np.float32) # + list(self.prev_actions)
        print((self.nearest_gem_pos[0]-px, self.nearest_gem_pos[1]-py)) 
        #print(self.observation_space)
        #for ex, ey in self.gameStateObj['enemies']:
        #    grid[ex, ey] = 6
        return np.clip(obs, 0, 1)

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

        #collect gem reward
        gem_reward = 0
        if self.prev_gem_count < len(self.levelObj['startState']['diamonds']) - len(self.gameStateObj['diamonds']):
            gem_reward = 100
            self.prev_gem_count = len(self.levelObj['startState']['diamonds']) - len(self.gameStateObj['diamonds'])
            self.steps_since_gem = 0
        
        
        if self.steps >= 3000: #timeout punishment
            reward = -100
            terminated = True
        elif self.dead: #death punishment
            reward = -50
            terminated = True
        elif len(self.gameStateObj['diamonds']) == 0 and (px, py) == self.gameStateObj['door']: #goal
            reward = 300
            #terminated = True
            self.level_index += 1
            if self.level_index < len(self.levels):
                self._load_level(self.level_index)
                self.steps = 0
                self.steps_since_gem = 0
                self.prev_gem_count = 0
                self.current_dist_to_gem, self.nearest_gem_pos = self._bfs_distance_to_nearest_diamond(self.blockedStone)
                self.prev_dist_to_gem = self.current_dist_to_gem
                terminated = False  # continue episode
            else:
                terminated = True
        else: #distance to gem reward
            reward = ((self.prev_dist_to_gem - self.current_dist_to_gem) + gem_reward)
            self.prev_dist_to_gem = self.current_dist_to_gem
            
            #if self.steps_since_gem >= 40:
            #    reward -= 0.1

        #punishment for stalling
        #reward -= 0.5

        print(self.currentAction)
        #if rock push left
        if(self.mapObj[px-1] and self.mapObj[py] == 'o' and self.currentAction == 1 ):
            reward += 50

        #if rock push left
        if(self.mapObj[px+1] and self.mapObj[py] == 'o' and self.currentAction == 3):
            reward += 50

        #punishment if same pos for 5 timesteps

        print("lastposcotunter:", self.lastPosCounter)
        if((abs(self.centerPos[0] - px) + abs(self.centerPos[1] - py)) < 4):
            self.lastPosCounter +=1
            reward -= 1
        else:
            self.lastPosCounter = 0
            self.centerPos = [px,py]

        if(self.lastPosCounter == 5):
            reward -= 10
            self.lastPosCounter = 0



        #print(reward)
        return reward, terminated

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
        self.clock.tick(2000) #fps

    def close(self):
        if self.screen:
            pygame.quit()
            self.screen = None
            self.clock = None
    
