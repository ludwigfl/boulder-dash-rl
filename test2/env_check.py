from stable_baselines3.common.env_checker import check_env
from boulderdash_env import BoulderDashEnv

env = BoulderDashEnv(level_index=0, render_mode="human")
check_env(env)

print("double check")

episodes = 50

for episode in range(episodes):
    done = False
    obs = env.reset()
    while not done:
        random_action = env.action_space.sample()
        print("action", random_action)
        obs, reward, done, trunc, info = env.step(random_action)
        print("reward", reward)