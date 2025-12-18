import time
from boulderdash_env import BoulderDashEnv
from stable_baselines3 import PPO
#from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from matplotlib import pyplot as plt
import numpy as np

LOG_DIR = './logs/'

level = 0
env = BoulderDashEnv(level_index=level, render_mode="human")
state = env.reset()
#print(state)
#print(state.shape)
#state, reward, done, info = env.step([env.action_space.sample()])
#state, reward, done, info = env.step([3])

"""plt.figure(figsize=(15, 10))
for idx in range(state.shape[3]):
    plt.subplot(1, 4, idx+1)
    plt.imshow(state[0][:,:,idx].T)
plt.show()"""

""""model = PPO.load(
    'models\\model_lvl0d', 
    env,
    verbose=1, 
    tensorboard_log=LOG_DIR,
)"""


model = PPO(
    'MlpPolicy', 
    env,
    verbose=1, 
    tensorboard_log=LOG_DIR,
)


timesteps = 300000
model.learn(total_timesteps=timesteps, progress_bar=True)
#print(model)
model.save(f"models\\model_lvl{level}d")
env.close()
#plt.imshow(state[0], cmap='tab20')  # transpose so x-axis = width, y-axis = height
#plt.show()
#print(env.action_space)
#print(env.observation_space.shape)
