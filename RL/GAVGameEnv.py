import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch as tf
import torch.nn as nn
import sys
import SockServer


class GAVActionSpace( spaces.Discrete ):

    def __init__( self, n, env ):
        spaces.Discrete.__init__( self, n )
        self.probs = np.array([0.5,1,1,0.3])
        self.probs = self.probs / np.sum( self.probs )
        #print("init invoked")
        GAVActionSpace.env = env



    def sample( self, mask = None, probability = None ):

        if self.env is None:
            print("self.env does not exist!")
            return  spaces.Discrete.sample(self, mask, probability=self.probs )

        px,py,bx,by,vx,vy = self.env.state[0], self.env.state[1], self.env.state[2], self.env.state[3], self.env.state[4], self.env.state[5]
        #print(f"sample player pos: {px}")

        prob = np.array( (0.5,0.5,0.5,0.07) )
        if np.sign(bx) == np.sign(px):

            if vx==0.0 and vy==0.0:
                #print("Jump")
                prob[3] = 1.0 

            if px>bx:
                #print("Forward")
                prob[1] = 1.0 

            if px<bx:
                #print("Backward")
                prob[2] = 1.0 

        else:
            if px>0.20:
                #print("Forward")
                prob[1] = 1.0 
            if px<0.20:
                #print("Backward")
                prob[2] = 1.0 
                
        prob = prob / np.sum(prob)
        #print(prob)
        r = spaces.Discrete.sample(self, mask, probability=prob )

        return r



class GAVGameEnv(gym.Env):
    """
    Same environment as before, just for context.
    """
    def __init__(self, port=1809, serversocket=None ):

        super(GAVGameEnv, self).__init__()

        print(" GAVGameEnv init ")
        """
        ACTION MAPPING 
        0: do nothing
        1: move forward
        2: move backward
        3: jump
        """
        #self.action_space = spaces.Discrete(4)
        self.action_space = GAVActionSpace(4, self )


        #float game_data[6] = { px,py,bx,by,bvx,bvy };
        self.observation_space = spaces.Box(low=-2.0, 
                                            high=2.0, 
                                            shape=(7,), dtype=np.float32)

        self.steps_left = 0
        if serversocket is None:
            self.server = SockServer.SockServer(host='0.0.0.0', port=port )
        else:
            self.server = serversocket 

        self.prev_game_status = None
        self.max_steps = 100
        self.max_touches = 10
        self.num_touches = 0


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = self.observation_space.sample()

        self.steps_left = self.max_steps
        self.prev_dist = None
        self.last_action = None

        GAVActionSpace.env = self

        return self.state, {}


    def step(self, action):

        if not self.server.is_client_connected():
            print("Waiting for clients...")
            self.server.wait_for_connection()

        #action=int(input("Action?"))
        #print("Action: ", action)

        # Send action
        action_sequence_num = self.steps_left
        action_with_sequence_num = action + action_sequence_num * 8
        #print("send action %d with seq num %d "%(action,action_sequence_num) )
        
        if not self.server.send_action( action_with_sequence_num ):
            print("Client disconnected.")
            return None, None, None, None, {}


        # Receive the payload
        while True:
            status = self.server.recv_status()

            if status is None:
                print("Client disconnected.")
                return None, None, None, None, {}

            received_seq_num = status[0] // 8
            game_status = status[0] % 8
            #print("received seq num %d (expected=%d), game_status %d"%(received_seq_num,action_sequence_num,game_status) )

            if received_seq_num == action_sequence_num:
                break

        
        """
        Game status:
        0: playing 
        1: win
        2: lose
        3: ball hit the player
         """
        #float game_data[6] = { px,py,bx,by,bvx,bvy };
        self.state[:6] = status[1:]

        self.steps_left -= 1

        px,py,bx,by,vx,vy = self.state[0], self.state[1], self.state[2], self.state[3], self.state[4], self.state[5]


        reward = 0

        dist_to_ball = np.sqrt( (bx - px)**2 )
        dist_to_center = np.sqrt( (bx - 0.19)**2 )

        #print("px,py: %3.3f %3.3f  - bx,by: %3.3f %3.3f. Dist: %3.3f "%(px,py,bx,by, dist_to_ball) )

        if np.sign(bx) == np.sign(px):
            # if the ball is on our side, try to catch it
            ball_dist_reward = 0.4*np.exp( -dist_to_ball*10.26)              
            #print("ball dist reward: %3.3f"%(ball_dist_reward) )
            #reward += ball_dist_reward
        else:
            # Ball on other side
            self.num_touches = 0
            center_dist_reward = 0.4*np.exp( -dist_to_center*10.26)              
            #print("center dist reward: %3.3f"%(center_dist_reward) )
            reward += center_dist_reward

        if vx==0.0 and vy==0.0:                     # ready to serve, do not waste time
            reward -= 0.1

        if game_status==1:
            reward += 1.0     # win
        elif game_status==2:
            reward -= 1.0       # lose
        elif game_status==3:    # ball hit
            self.num_touches += 1
            touches_ratio = self.num_touches/self.max_touches
            touch_reward = (1.0-touches_ratio) * 1.0  + touches_ratio * (-0.2)      # ball hit reward (high for first hit, decreasing thereafter)
            #print("touch reward: ", touch_reward )
            reward += touch_reward 


        touches_ratio = self.num_touches/self.max_touches
        self.state[6] = touches_ratio

        #import time
        #time.sleep(1/100.0)
        #print("%f touches, reward= %f"%(self.state[6], reward) )

        terminated = False
        if game_status==1 or game_status==2:
            terminated = True
            self.num_touches = 0

        truncated = (self.steps_left <= 0)


        return self.state, reward, terminated, truncated, {}
