from boulderdash_env import BoulderDashEnv
from stable_baselines3 import PPO
import sys

if __name__ == "__main__":
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rs = int(sys.argv[2]) if len(sys.argv) > 2 else 2000 #20 is good for viewing, 2000 for training
    timesteps = int(sys.argv[3]) if len(sys.argv) > 3 else 100000 #100k is usually a pretty good number

    LOG_DIR = './logs/'
    model_name = "model_v1-15"

    env = BoulderDashEnv(level_index=level, render_mode="human", render_speed=rs)
    state = env.reset()

    model = PPO(
        'MlpPolicy', 
        env,
        verbose=1, 
        tensorboard_log=LOG_DIR,
    )

    """model = PPO.load(
        'models\\model_v1-14', 
        env,
        verbose=1, 
        tensorboard_log=LOG_DIR,
    )"""

    model.learn(total_timesteps=timesteps, progress_bar=True)
    model.save(f"models\\{model_name}")
    env.close()
