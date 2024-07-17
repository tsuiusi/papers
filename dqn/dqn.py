import mlx
import mlx.nn as nn
import mlx.core as mx
import mlx.optimizers as optim

import os
import sys
import pickle
import time
import random
import numpy as np
from collections import deque, namedtuple

"""
replicating https://www.cs.toronto.edu/~vmnih/docs/dqn.pdf

1. make network
2. make policy
3. setup environment
4. make training loop
5. setup loss/accuracy graph

what it does (in a single episode):
    * it looks ahead and picks the action that it predicts will take 
    * execute action in emulator, observe next state and reward
    * store transition in replay memory
    * sample random batch of transitions from replay memory
    * use samples to perform gradient descent
"""

class DQN(nn.Module):
    def __init__(self, input_dims: int, output_dims: int):
        self.conv1 = nn.Conv2d(in_channels=4, out_channels=16, kernel_size=8, stride=4) # depends on the input, might change later
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=4, stride=2)

        self.fc1 = nn.Linear(input_dims=512, output_dims=256)
        self.fc2 = nn.Linear(input_dims=256, output_dims=output_dims) # depends on the no. actions available, we assume an arbitrary atari game so 4
        self.relu = nn.ReLU()

    def __call__(self, x):
        print(x.shape)
        x = self.conv1(x)
        x = self.relu(x)

        x = self.conv2(x)
        x = self.relu(x)

        x = mx.flatten(x)

        x = self.fc1(x)
        x = self.fc2(x)
        return x

Transition = namedtuple('Transition',('state', 'action', 'next_state', 'reward'))

class ReplayBuffer(object):
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        self.memory.append(Transition(*args))

    def sample(self, batch_size: int):
        return random.sample(self.memory, batch_size)

    def _len(self):
        return len(self.memory)


