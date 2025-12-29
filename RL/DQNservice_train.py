import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import DQN 
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor
import torch as tf
import torch.nn as nn
import sys
import SockServer
from GAVGameEnv import GAVGameEnv




# --- THE SAFE DQN CONFIGURATION ---

# 1. Initialize Environment
env = GAVGameEnv()
#env = VecFrameStack(env, n_stack=4)
#env = DummyVecEnv([lambda: GAVGameEnv()])
#env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)

## Define custom architecture
#policy_kwargs = dict(
#    activation_fn=nn.ReLU,
#    net_arch=dict(pi=[128, 64, 64, 32], vf=[64,64]) # pi = Actor, vf = Critic
#)
#
#policy_kwargs = dict(activation_fn=nn.ReLU,
#                     net_arch=dict(pi=[32, 32], vf=[32, 32]))
#



def linear_schedule(initial_value, final_value):
    def func(progress_remaining):
        return progress_remaining * initial_value + (1.0-progress_remaining) * final_value

    return func



model = DQN(
    "MlpPolicy", 
    env, 
    gamma=0.96,
    #policy_kwargs=policy_kwargs,
    policy_kwargs = dict(activation_fn=tf.nn.Tanh, net_arch=[64,64,32,16,16]),
    tensorboard_log="./dqn_tensorboard/",
    verbose=1,
    
    # --- A. TIMING SETTINGS (Crucial for you) ---
    train_freq=(1, "episode"), 
    
    # When we DO stop to train, how many updates should we do?
    gradient_steps=2000,

    
    # Just watch and fill the memory. Prevents training on garbage data.
    learning_starts=20_000, 
    
    # 2. How many past memories to keep. 
    buffer_size=2_000_000, 
    
    # 3. Exploration decay.
    exploration_fraction=0.6, 
    exploration_final_eps=0.07,
    exploration_initial_eps=1.0,

    # 4. Reference Network Update
    target_update_interval=200,

    # Learning rate
    learning_rate=1e-3
)

# --- TRAINING ---

phase0 = True
phase1 = True
phase2 = True
phase3 = True



if phase0:
    # Phase 1
    print("Training phase 0")

    # Initial random moves
    model.learn(total_timesteps=20_000, reset_num_timesteps=True)

    for i in range(5):
        model.learn(total_timesteps=10_000, reset_num_timesteps=True)
        env.max_steps += 100

    model.save("dqn_phase0")


if phase1:
    # Phase 1
    print("Training phase 1")

    custom_objects = { 'learning_rate': 1e-4,
                       'exploration_fraction':0.5,
                       'exploration_initial_eps':0.99,
                       'exploration_final_eps':0.2, 
                       'target_update_interval':500 
                     }
    model = DQN.load("dqn_phase0", env, custom_objects = custom_objects )
    env.max_steps = 1000
    model.learn(total_timesteps=100_000, reset_num_timesteps=True)
    model.save("dqn_phase1")


if phase2:
    # Phase 2
    print("Training phase 2")

    custom_objects = { 'learning_rate': linear_schedule(5e-4, 5e-5 ),
                       'exploration_fraction':0.10,
                       'exploration_initial_eps':0.10,
                       'exploration_final_eps':0.10, 
                       'target_update_interval':2000,
                       'gradient_steps':1500,
                     }

    model = DQN.load("dqn_phase1", env, custom_objects = custom_objects)
    env.max_steps = 2000

    model.learn(total_timesteps=280_000, reset_num_timesteps=False)
    model.save("dqn_phase2")


if phase3:
    # Phase 3
    print("Training phase 3")

    eval_env = GAVGameEnv( serversocket=env.server )
    eval_env.max_steps = 4000

    eval_callback = EvalCallback(
        Monitor( eval_env ),
        best_model_save_path="./logs/best_model/",
        log_path="./logs/results/",
        eval_freq=10_000,        # Check performance every 5000 steps
        n_eval_episodes=100,    # Number of episodes to play for evaluation
        deterministic=True,    # Test without exploration noise (Pure skill)
        render=False,
        verbose=1
    )

    custom_objects = { 'learning_rate': linear_schedule(5e-5, 0),
                       'exploration_fraction':0.01,
                       'exploration_initial_eps':0.07,
                       'exploration_final_eps':0.07, 
                       'target_update_interval':5_000,
                       'gradient_steps':4000,
                     }

    model = DQN.load("dqn_phase2", env, custom_objects = custom_objects)
    env.max_steps = 4000

    model.learn(total_timesteps=800_000, reset_num_timesteps=False, callback=eval_callback )
    model.save("dqn_phase3")
