from typing import Dict, Union

import GPy
from GPy.kern import Kern
from safeopt import SafeOptSwarm

from gym_microgrid.agents.staticctrl import StaticControlAgent
from gym_microgrid.agents.util import MutableParams
from gym_microgrid.controllers import Controller

import matplotlib.pyplot as plt

import numpy as np


class SafeOptAgent(StaticControlAgent):
    def __init__(self, mutable_params: Union[dict, list], kernel: Kern, ctrls: Dict[str, Controller],
                 observation_action_mapping: dict):
        self.params = MutableParams(
            list(mutable_params.values()) if isinstance(mutable_params, dict) else mutable_params)
        self.kernel = kernel

        self.episode_reward = None
        self.optimizer = None
        super().__init__(ctrls, observation_action_mapping)

    def reset(self):
        # reinstantiate kernel
        # self.kernel = type(self.kernel)(**self.kernel.to_dict())
        self.kernel = GPy.kern.Matern32(input_dim=1, lengthscale=.01)

        self.params.reset()
        self.optimizer = None
        self.episode_reward = 0
        return super().reset()

    def observe(self, reward, terminated):
        self.episode_reward += reward or 0
        if terminated:
            # safeopt update step
            self.update_params()
            # reset episode reward
            self.episode_reward = 0
        # on other steps we don't need to do anything

    def update_params(self):
        if self.optimizer is None:
            bounds = [(-0.1, 0.2)]
            noise_var = 0.05 ** 2
            gp = GPy.models.GPRegression(np.array([self.params[:]]), np.array([[self.episode_reward]]), self.kernel,
                                         noise_var=noise_var)
            self.optimizer = SafeOptSwarm(gp, 0., bounds=bounds, threshold=1)
        else:
            self.optimizer.add_new_data_point(self.params[:], self.episode_reward)
        self.params[:] = self.optimizer.optimize()

    def render(self):
        plt.figure
        self.optimizer.plot(1000)
        plt.show()
