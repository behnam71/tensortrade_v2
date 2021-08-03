  
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
# limitations under the License
import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from time import sleep

from typing import List, Union
from ccxt import BadRequest

from tensortrade.oms.exchanges import Exchange
from tensortrade.oms.instruments import TradingPair, BTC, USDT


class CCXTExchange():
    """An exchange for trading on CCXT-supported cryptocurrency exchanges."""
    def __init__(self, 
                 exchange: Union[ccxt.Exchange, str],
                 credentials: dict):
        self._exchange_str = exchange
        self._exchange = getattr(
            ccxt, self._exchange_str
        )() if isinstance(self._exchange_str, str) else self._exchange_str
        self._exchange.urls['api'] = self._exchange.urls['test'] # use the testnet
        
        self._exchange.enableRateLimit = True
        
        self._exchange.apiKey = credentials['apiKey']
        self._exchange.secret = credentials['secret']
        self._base_instrument = USDT; self._quote_instrument = BTC
        
        self._BTC_USDT_PAIR = TradingPair(USDT, BTC)
        self._observation_pairs = [self._BTC_USDT_PAIR]
        self._observation_symbols = [
            self.pair_to_symbol(pair) for pair in self._observation_pairs
        ]
        self._timeframe = '1m'

        self.observations = pd.DataFrame([], columns=self.observation_columns())
        self._f_time = self.UTC_Time()
        self.streams = 0
        
        self._exchange.load_markets()
                
        
    def observation_columns(self) -> List[str]:
        return np.array([[
            '{}:open'.format(symbol), '{}:high'.format(symbol), '{}:low'.format(symbol), 
            '{}:close'.format(symbol), '{}:volume'.format(symbol),
        ] for symbol in self._observation_symbols]).flatten()

    def UTC_Time(self):
        now_utc = datetime.now(timezone.utc)
        now_utc = datetime.strftime(now_utc, "%Y-%m-%d %H:%M:00")
        return datetime.strptime(now_utc, "%Y-%m-%d %H:%M:00")

    def next_observation(self, 
                         window_size: int = 1) -> pd.DataFrame:
        self.observations = pd.DataFrame([], columns=self.observation_columns())
        for symbol in self._observation_symbols:
            while self._f_time == self.UTC_Time():
                sleep(1)
            self.ohlcv = self._exchange.fetch_ohlcv(
                self._observation_symbols[0],
                timeframe=self._timeframe,
                limit=1,
            )
            self.observations = pd.DataFrame.from_records(self.ohlcv)
            self.observations.columns = ['{}:date'.format(symbol), '{}:open'.format(symbol), '{}:high'.format(symbol), '{}:low'.format(symbol),
                                         '{}:close'.format(symbol), '{}:volume'.format(symbol)]
        for i in range(0, len(self.observations)):
            self.observations.loc[i, 'BTC:date'] = datetime.utcfromtimestamp(
                self.observations.loc[i, 'BTC:date']/1000
            )
        self._f_time = self.observations.loc[len(self.observations)-1, 'BTC:date']

        self.observations = pd.concat(
            [self._data_frame, self.observations],
            ignore_index=True, 
            sort=False
        )
        self._data_frame = self.observations
        if len(self._data_frame) >= window_size:
            self._data_frame = self._data_frame.iloc[-(window_size):]
        
        return self.observations.to_numpy()

    
    def pair_to_symbol(self, 
                       pair: 'TradingPair') -> str:
        return '{}/{}'.format(pair.quote.symbol, pair.base.symbol)

    def quote_price(self, 
                    pair: 'TradingPair'):
        symbol = self.pair_to_symbol(pair)
        try:
            return float(self._exchange.fetch_ticker(symbol)['close'])
        except BadRequest:
            return np.inf
