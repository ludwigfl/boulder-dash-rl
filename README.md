# Boulder Dash (PyGame)

This project implements a Gymnasium-compatible Boulder Dash environment and trains an agent using Stable-Baselines3 PPO to solve Boulder Dash levels.

The environment wraps an existing Boulder Dash game logic and provides observations, rewards, and rendering via Pygame.

Original creator of this Boulder Dash game is made by Olivier Charles, GIT:[Olivier Charles Boulder Dash](https://github.com/Olivier7355/boulder-dash)

# Requirements

- Python 3.9 or newer
- Pygame 2.1.2 or newer

# Python packages

Install the required dependencies:

```
pip install gymnasium stable-baselines3 pygame numpy
```

# Training the Agent

```
python RL_code/train.py [level] [render_speed] [timesteps]
```

# Running a Trained Agent

```
python RL_code/run_trained_agent.py [level] [render_speed]
```