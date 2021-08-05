# Copyright 2020 The TensorTrade Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License
import uuid
import logging
from typing import Union, Tuple, List, Dict, Any

import gym
import numpy as np
import ccxt

from tensortrade.oms.services.execution.ccxt import CCXTExchange
from tensortrade.core import TimeIndexed, Clock, Component
from tensortrade.env.generic import (
    ActionScheme,
    RewardScheme,
    Observer,
    Stopper,
    Informer,
    Renderer
)
from tensortrade.features import FeaturePipeline
from tensortrade.features.indicators.talib_indicator import TAlibIndicator


class TradingEnv_v1(gym.Env, TimeIndexed):
    """A trading environment made for use with Gym-compatible reinforcement
    learning algorithms.
    Parameters
    ----------
    action_scheme : `ActionScheme`
        A component for generating an action to perform at each step of the
        environment.
    reward_scheme : `RewardScheme`
        A component for computing reward after each step of the environment.
    observer : `Observer`
        A component for generating observations after each step of the
        environment.
    informer : `Informer`
        A component for providing information after each step of the
        environment.
    renderer : `Renderer`
        A component for rendering the environment.
    kwargs : keyword arguments
        Additional keyword arguments needed to create the environment.
    """
    agent_id: str = None
    episode_id: str = None
    print("4444444444444444444444444444444444444444444444444444444444444444")

    def __init__(self,
                 action_scheme: ActionScheme,
                 reward_scheme: RewardScheme,
                 stopper: Stopper,
                 informer: Informer,
                 window_size: int,
                 **kwargs) -> None:
        super().__init__()
        print("555555555555555555555555555555555555555555555555555555555555555522")
        self.clock = Clock()

        self.action_scheme = action_scheme
        self.reward_scheme = reward_scheme
        self.stopper = stopper
        self.informer = informer
        print("555555555555555555555555555555555555555555555555555555555555555577")

        for c in self.components.values():
            c.clock = self.clock

        self.action_space = action_scheme.action_space

        credentials = { 
            'apiKey': 'SmweB9bNM2qpYkgl4zaQSFPpSzYpyoJ6B3BE9rCm0XYcAdIE0b7n6bm11e8jMwnI',  
            'secret': '8x6LtJztmIeGPZyiJOC7lVfg2ixCUYkhVV7CKVWq2LVlPh8mo3Ab7SMkaC8qTZLt',
        }
        self.ccxt = CCXTExchange(
            exchange='binance',
            credentials=credentials,
        )
        
        self._window_size = window_size
        
        with open("/mnt/c/Users/BEHNAMH721AS.RN/OneDrive/Desktop/indicators.txt", "r") as file:
            indicators_list = eval(file.readline())
        TAlib_Indicator = TAlibIndicator(indicators_list)
        self.feature_pipeline = FeaturePipeline(
            steps=[TAlib_Indicator]
        )
            
        self._enable_logger = kwargs.get('enable_logger', True)
        if self._enable_logger:
            self.logger = logging.getLogger(kwargs.get('logger_name', __name__))
            self.logger.setLevel(kwargs.get('log_level', logging.DEBUG))

            
    @property
    def components(self) -> 'Dict[str, Component]':
        """The components of the environment. (`Dict[str,Component]`, read-only)"""
        return {
            "action_scheme": self.action_scheme,
            "reward_scheme": self.reward_scheme,
            "stopper": self.stopper,
            "informer": self.informer,
        }

    
    @property
    def feature_pipeline(self) -> FeaturePipeline:
        """The pipeline of feature transformations to pass the observations through at each time step."""
        return self._feature_pipeline

    @feature_pipeline.setter
    def feature_pipeline(self, feature_pipeline: Union[FeaturePipeline, str] = None):
        self._feature_pipeline = features.get(feature_pipeline) if isinstance(
            feature_pipeline, str
        ) else feature_pipeline

    def _next_observation(self) -> np.ndarray:
        observation = self.ccxt.next_observation(self._window_size)
        if self._feature_pipeline is not None:
            observation = self._feature_pipeline.transform(observation)
        
        if len(observations) < self._window_size:
            size = self.window_size - len(observations)
            padding = np.zeros(size, len(self.observation_columns()))
            padding = pd.DataFrame(padding, columns=self.observation_columns())
            observations = pd.concat([padding, observation], ignore_index=True, sort=False)
                
        observations = self.observations.select_dtypes(include='number')
        if isinstance(observations, pd.DataFrame):
            observations = observations.fillna(0, axis=1)
        observations = np.nan_to_num(self.observations)
        
        return observations.to_numpy()
        
        
    def step(self, action: Any) -> 'Tuple[np.array, float, bool, dict]':
        """Makes on step through the environment.
        Parameters
        ----------
        action : Any
            An action to perform on the environment.
        Returns
        -------
        `np.array`
            The observation of the environment after the action being
            performed.
        float
            The computed reward for performing the action.
        bool
            Whether or not the episode is complete.
        dict
            The information gathered after completing the step.
        """
        print("6666666666666666666666666666666666666666666666666666666666666666")
        self.action_scheme.perform(self, action)

        obs = self._next_observation()
        reward = self.reward_scheme.reward(self)
        done = self.stopper.stop(self)
        info = self.informer.info(self)

        self.clock.increment()
        return obs, reward, done, info

    
    def reset(self) -> 'np.array':
        """Resets the environment.
        Returns
        -------
        obs : `np.array`
            The first observation of the environment.
        """
        self.episode_id = str(uuid.uuid4())
        self.clock.reset()
        print("7777777777777777777777777777777777777777777777777777777777777777")

        for c in self.components.values():
            if hasattr(c, "reset"):
                c.reset()

        obs = self._next_observation()

        self.clock.increment()
        return obs
