from boulderdash_env import BoulderDashEnv
from stable_baselines3 import PPO

level = 0
model = PPO.load(f"models\\model_lvl{level}d")  # Load trained agent
env = BoulderDashEnv(level_index=level, render_mode="human")
episodes = 50

for episode in range(episodes):
    done = False
    obs, info = env.reset()
    while not done:
        action, _ = model.predict(obs)
        #random_action = env.action_space.sample()
        obs, reward, done, trunc, info = env.step(action)

        #state, reward, done, trunc, info = env.step(action)