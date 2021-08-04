# Copyright 2019 The TensorTrade Authors.
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
# limitations under the License.
import numpy as np
import pandas as pd

import talib
from gym import Space
from copy import copy
from abc import abstractmethod
from typing import Union, List, Callable

from tensortrade.features import FeatureTransformer


class TAlibIndicator(FeatureTransformer):
    """Adds one or more TAlib indicators to a data frame, based on existing open, high, low, and close column values."""
    def __init__(self, 
                 indicators: List[str],
                 lows: Union[List[float], List[int]] = None, 
                 highs: Union[List[float], List[int]] = None,
                 **kwargs):
        self._indicator_names = [
            indicator[0].upper() for indicator in indicators
        ]
        self._indicator_args = {indicator[0]: indicator[1]['args'] for indicator in indicators}
        self._indicator_params = {indicator[0]: indicator[1]['params'] for indicator in indicators}
        self._indicators = [getattr(talib, name.split('-')[0]) for name in self._indicator_names]
        
        self.db = pd.DataFrame(columns=['BTC/USDT:date', 'BTC/USDT:open', 'BTC/USDT:high', 'BTC/USDT:low', 'BTC/USDT:close', 'BTC/USDT:volume', 
                                        'BTC', 'USDT', 'BTC:pending', 'USDT:pending'], dtype=float)
        
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = pd.DataFrame(X)
        self.db = pd.concat(
            [self.db, X],
            ignore_index=True, 
            sort=False
        )
        self.db.drop_duplicates(subset=['BTC/USDT:date'], 
                                keep='first', 
                                inplace=True)
        self.db = self.db.reset_index(drop=True)
        for idx, indicator in enumerate(self._indicators):
            indicator_name = self._indicator_names[idx]
            indicator_args = [
                self.db[arg].values for arg in self._indicator_args[indicator_name]
            ]
            indicator_params = self._indicator_params[indicator_name]
            if indicator_name == 'MACD':
                macd , macdsignal , macdhist  = indicator(*indicator_args, **indicator_params)
                X["macd"] = macd[-len(X):]; X["macd_signal"] = macdsignal[-len(X):]; X["macd_hist"] = macdhist[-len(X):]
            elif indicator_name == 'BBANDS':
                upper, middle, lower = indicator(*indicator_args, **indicator_params)
                X["bb_upper"] = upper[-len(X):]; X["bb_middle"] = middle[-len(X):]; X["bb_lower"] = lower[-len(X):]
            elif indicator_name == 'STOCH':
                slowk , slowd = indicator(*indicator_args, **indicator_params)
                X["slowk"] = slowk[-len(X):]; X["slowd"] = slowd[-len(X):]
            else:
                value = indicator(*indicator_args, **indicator_params)
                X[indicator_name] = value[-len(X):]

        self.db = self.db.reset_index(drop=True)
        return X
