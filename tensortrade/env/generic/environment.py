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
import pandas as pd

import gym
import numpy as np

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


class TradingEnv(gym.Env, TimeIndexed):
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

    def __init__(self,
                 action_scheme: ActionScheme,
                 reward_scheme: RewardScheme,
                 observer: Observer,
                 stopper: Stopper,
                 informer: Informer,
                 renderer: Renderer,
                 window_size: int,
                 t_signal: bool,
                 **kwargs) -> None:
        super().__init__()
        self.clock = Clock()
        
        self.stopper = stopper
        self.action_scheme = action_scheme
        self.reward_scheme = reward_scheme
        self.observer = observer
        self.informer = informer
        self.renderer = renderer

        for c in self.components.values():
            c.clock = self.clock

        self.action_space = action_scheme.action_space
        self.observation_space = observer.observation_space

        self._t_signal = t_signal
        
        if not(self._t_signal):
            credentials = { 
                'apiKey': 'SmweB9bNM2qpYkgl4zaQSFPpSzYpyoJ6B3BE9rCm0XYcAdIE0b7n6bm11e8jMwnI',  
                'secret': '8x6LtJztmIeGPZyiJOC7lVfg2ixCUYkhVV7CKVWq2LVlPh8mo3Ab7SMkaC8qTZLt',
            }
            self.ccxt = CCXTExchange(
                exchange='binance',
                credentials=credentials,
            )
        
        self._window_size = window_size
        
        with open("./crypto-v2/indicators.txt", "r") as file:
            indicators_list = eval(file.readline())
        TAlib_Indicator = TAlibIndicator(indicators_list, self._window_size)
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
            "observer": self.observer,
            "stopper": self.stopper,
            "informer": self.informer,
            "renderer": self.renderer
        }
    
    @property
    def feature_pipeline(self) -> FeaturePipeline:
        """The pipeline of feature transformations to pass the observations through at each time step."""
        return self._feature_pipeline

    @feature_pipeline.setter
    def feature_pipeline(self, feature_pipeline: Union[FeaturePipeline, str] = None):
        self._feature_pipeline = features.get(
            feature_pipeline
        ) if isinstance(feature_pipeline, str) else feature_pipeline

    def _next_observation(self) -> np.ndarray:
        observation = self.ccxt.next_observation(self._window_size)
        if self._feature_pipeline is not None:
            observation = self._feature_pipeline.transform(observation)

        if len(observation) < self._window_size:
            size = self._window_size - len(observation)
            padding = np.zeros((size, len(observation.columns)))
            padding = pd.DataFrame(padding, columns=observation.columns)
            observation = pd.concat([padding, observation], ignore_index=True, sort=False)

        observation.set_index('date', inplace = True)
        observation = observation.add_prefix("BTC:")
        observation = observation.select_dtypes(include='number')
        
        if isinstance(observation, pd.DataFrame):
            observation = observation.fillna(0, axis=1)

        return observation.to_numpy()
        
        
    def step(self, action: Any) -> 'Tuple[np.array, float, bool, dict]':
        """Makes on step through the environment.
        Parameters
        ----------
        action : Any (An action to perform on the environment.)
        
        Returns
        -------
        np.array (The observation of the environment after the action being performed.)
        float (The computed reward for performing the action.)
        bool (Whether or not the episode is complete.)
        dict (The information gathered after completing the step.)
        """
        self.action_scheme.perform(self, action, self._t_signal)
        
        if self._t_signal:
            obs = self.observer.observe(self)
            reward = self.reward_scheme.reward(self)
            done = self.stopper.stop(self)
            info = self.informer.info(self)
            self.clock.increment()
        else:
            obs = self._next_observation()
            print("Online Observation:"); print(obs)
            return obs
        
        return obs, reward, done, info
    
    
    def reset(self) -> 'np.array':
        """Resets the environment.
        Returns
        -------
        obs : np.array
            The first observation of the environment.
        """
        self.episode_id = str(uuid.uuid4())
        self.clock.reset()
        for c in self.components.values():
            if hasattr(c, "reset"):
                c.reset()

        if self._t_signal:
            obs = self.observer.observe(self)
        else:
            obs = self._next_observation()
        
        self.clock.increment()
        return obs
    
    def render(self, **kwargs) -> None:
        """Renders the environment."""
        self.renderer.render(self, **kwargs)

    def save(self) -> None:
        """Saves the rendered view of the environment."""
        self.renderer.save()

    def close(self) -> None:
        """Closes the environment."""
        self.renderer.close()
