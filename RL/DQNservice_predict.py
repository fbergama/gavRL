import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import DQN 
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.vec_env import VecFrameStack
import torch as tf
import torch
import torch.nn as nn
import sys
import SockServer
from GAVGameEnv import GAVGameEnv


import cv2 as cv
import serial
from serial.serialutil import SerialException


def pack_bools_to_bytes(arr):
    """
    Converts a boolean array to a bytes object.
    Each column of 8 booleans becomes 1 byte.
    """
    # We pack along the first axis (the '8' dimension)
    # 'big' or 'little' endianness depends on your receiving hardware
    packed_bytes = np.packbits(arr, axis=0, bitorder='big')
    return packed_bytes.tobytes()


stop_icon = np.array( [ [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0],
                        [0,0,0,1,1,0,0,0],
                        [0,0,0,1,1,0,0,0],
                        [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0] ], dtype=np.bool )

left_icon = np.array( [ [0,0,0,0,0,0,0,0],
                        [0,0,0,1,0,0,0,0],
                        [0,0,1,1,0,0,0,0],
                        [0,1,1,0,0,0,0,0],
                        [0,0,1,1,0,0,0,0],
                        [0,0,0,1,0,0,0,0],
                        [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0] ], dtype=np.bool )


icon_action_mapping = ( stop_icon, left_icon, left_icon[:,::-1], left_icon.T )


# --- THE SAFE DQN CONFIGURATION ---

# 1. Initialize Environment
env = GAVGameEnv( port=1810 )

#model = DQN(
#    "MlpPolicy", 
#    env, 
#    #policy_kwargs=policy_kwargs,
#    policy_kwargs = dict(activation_fn=tf.nn.Tanh, net_arch=[64,32,32,16,16]),
#    verbose=1,
#    batch_size=1,
#    
#    # --- A. TIMING SETTINGS (Crucial for you) ---
#    train_freq=(1000, "episode"), 
#    
#    # When we DO stop to train, how many updates should we do?
#    # -1 means: "If the match lasted 100 steps, do 100 gradient updates."
#    # This keeps the training ratio 1:1 without lagging the game play.
#    #gradient_steps=-1,
#    gradient_steps=1,
#
#    # --- B. STABILITY SETTINGS (The "Safe" part) ---
#    
#    # 1. Don't train on the first 10000 steps. 
#    # Just watch and fill the memory. Prevents training on garbage data.
#    learning_starts=0, 
#    
#    # 2. How many past memories to keep. 
#    buffer_size=1, 
#    
#    # 3. Exploration decay.
#    # Start at 100% random, drop to 5% random over the first 10% of training.
#    exploration_fraction=0.6, 
#    exploration_final_eps=0.07,
#)
#
env.training = False 

print("Loading model...")
custom_objects = {
        "device":"cpu"
        }
model = DQN.load("logs_28012026/best_model/best_model", env, custom_objects=custom_objects )

obs, _ = env.reset()


# 1. Setup a dictionary to store the outputs
activations = {}

# 2. Define the "Hook" function
# This function runs automatically whenever data passes through a layer
def get_activation(name):
    def hook(model, input, output):
        # 'output' is the tensor coming OUT of the layer
        # We detach it from the graph and move to CPU/Numpy for rendering
        activations[name] = output.detach().cpu().numpy()
    return hook

# 3. Register the hooks
# We loop through all sub-layers of the Q-Network and attach the wiretap
print("Registering hooks")
for name, layer in model.policy.q_net.named_modules():
    # We are interested in Linear layers (neurons) and Activations (ReLU/Tanh)
    if isinstance(layer, nn.Tanh):
        #print(f" - Watching: {name} { "Tanh" if isinstance(layer,nn.Tanh) else "linear" }")
        layer.register_forward_hook(get_activation(name))


ser = None
try:
    ser = serial.Serial('/dev/cu.usbserial-1420', 115200, timeout=1)
    print("Serial port ok")
except SerialException:
    print("Unable to open serial port, skipping...")


try:
    while True:

        obs_t = torch.tensor( np.array(obs, dtype=np.float32 ).reshape(1,-1) ).to(device="cpu")

        with torch.no_grad():
            q_values = model.policy.q_net(obs_t)
            action = np.argmax( q_values.cpu().numpy() )
            #print(action)


            neuron_activations = []
            for layer_name, output_data in activations.items():
                # output_data shape will be (1, N_Neurons)
                #print(f"Layer {layer_name}: {output_data.shape}")
                #print(output_data)

                neuron_activations.append( np.reshape( output_data, (8,-1) ) )

            all_activations = np.concatenate( neuron_activations, axis=1 )
            
            # Linear region for tanh(x) = -0.5 ... 0.5 ( -0.2<x<0.2 )
            all_activations = (np.abs(all_activations)<0.5).astype(np.uint8) * 255

            _w,_h = all_activations.shape[1], all_activations.shape[0]

            data = np.concatenate( [all_activations, icon_action_mapping[action] ], axis=1 )

            payload = pack_bools_to_bytes(data)

            if ser is not None:
                #print("Serial write")
                bytes_written = ser.write(payload)


            all_activations_big = cv.resize( all_activations, dsize=(_w*32,_h*32), interpolation=cv.INTER_NEAREST ) 
            del _w, _h
            cv.imshow( "neurons in linear region", all_activations_big )
            cv.waitKey(1)


        obs, reward, terminated, truncated, info = env.step(action)

        if (obs is None) or terminated or truncated:
            obs, _ = env.reset()

except KeyboardInterrupt:
    print("")
    print("Exiting...")
    if ser is not None:
        ser.close()
