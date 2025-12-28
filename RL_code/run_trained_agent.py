from boulderdash_env import BoulderDashEnv
from stable_baselines3 import PPO
import sys

if __name__ == "__main__":
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rs = int(sys.argv[2]) if len(sys.argv) > 2 else 20 #20 is good for viewing, 2000 for training
    
    model_name = "model_v1-14"
    model = PPO.load(f"models\\{model_name}")  # Load trained agent
    env = BoulderDashEnv(level_index=level, render_mode="human", render_speed=rs)
    episodes = 20

    for episode in range(episodes):
        done = False
        trunc = False
        obs, info = env.reset()
        while not done and not trunc:
            action, _ = model.predict(obs)
            obs, reward, done, trunc, info = env.step(action)
