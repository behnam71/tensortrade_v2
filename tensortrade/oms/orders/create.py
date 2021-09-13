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
from tensortrade.oms.instruments import ExchangePair
from tensortrade.oms.wallets import Portfolio
from tensortrade.oms.orders import Order, OrderSpec, TradeSide, TradeType, Order_v1
from tensortrade.oms.orders.criteria import Stop, Limit


def market_order(side: "TradeSide",
                 exchange_pair: "ExchangePair",
                 price: float,
                 size: float,
                 portfolio: "Portfolio",
                 t_signal: bool) -> "Order":
    """Creates a market order.

    Parameters
    ----------
    side : `TradeSide`
        The side of the order.
    exchange_pair : `ExchangePair`
        The exchange pair to perform the order for.
    price : float
        The current price.
    size : float
        The size of the order.
    portfolio : `Portfolio`
        The portfolio being used in the order.

    Returns
    -------
    `Order`
        A market order.
    """

    instrument = side.instrument(exchange_pair.pair)
    order = Order(
        step=portfolio.clock.step,
        side=side,
        trade_type=TradeType.MARKET,
        exchange_pair=exchange_pair,
        quantity=(size * instrument),
        portfolio=portfolio,
        price=price,
        t_signal=t_signal
    )

    return order


def limit_order(side: "TradeSide",
                exchange_pair: "ExchangePair",
                limit_price: float,
                size: float,
                portfolio: 'Portfolio',
                t_signal: bool,
                start: int = None,
                end: int = None):
    """Creates a limit order.

    Parameters
    ----------
    side : `TradeSide`
        The side of the order.
    exchange_pair : `ExchangePair`
        The exchange pair to perform the order for.
    limit_price : float
        The limit price of the order.
    size : float
        The size of the order.
    portfolio : `Portfolio`
        The portfolio being used in the order.
    start : int, optional
        The start time of the order.
    end : int, optional
        The end time of the order.

    Returns
    -------
    `Order`
        A limit order.
    """
    side = TradeSide[side]

    instrument = side.instrument(exchange_pair.pair)
    order = Order(
        step=portfolio.clock.step,
        side=side,
        trade_type=TradeType.LIMIT,
        exchange_pair=exchange_pair,
        quantity=(size * instrument),
        portfolio=portfolio,
        price=limit_price,
        t_signal=t_signal,
        start=start,
        end=end
    )

    return order


def hidden_limit_order(side: "TradeSide",
                       exchange_pair: "ExchangePair",
                       limit_price: float,
                       size: float,
                       portfolio: "Portfolio",
                       t_signal: bool,
                       start: int = None,
                       end: int = None):
    """Creates a hidden limit order.

    Parameters
    ----------
    side : `TradeSide`
        The side of the order.
    exchange_pair : `ExchangePair`
        The exchange pair to perform the order for.
    limit_price : float
        The limit price of the order.
    size : float
        The size of the order.
    portfolio : `Portfolio`
        The portfolio being used in the order.
    start : int, optional
        The start time of the order.
    end : int, optional
        The end time of the order.

    Returns
    -------
    `Order`
        A hidden limit order.
    """
    side = TradeSide[side]
    instrument = side.instrument(exchange_pair.pair)

    order = Order(
        step=portfolio.clock.step,
        side=side,
        trade_type=TradeType.MARKET,
        exchange_pair=exchange_pair,
        quantity=(size * instrument),
        portfolio=portfolio,
        price=limit_price,
        t_signal=t_signal,
        criteria=Limit(limit_price=limit_price),
        start=start,
        end=end,
    )

    return order


def risk_managed_order(side: "TradeSide",
                       trade_type: "TradeType",
                       exchange_pair: "ExchangePair",
                       price: float,
                       quantity: "Quantity",
                       down_percent: float,
                       up_percent: float,
                       portfolio: "Portfolio",
                       t_signal: bool,
                       start: int = None,
                       end: int = None):
    """Create a stop order that manages for percentages above and below the
    entry price of the order.

    Parameters
    ----------
    side : `TradeSide`
        The side of the order.
    trade_type : `TradeType`
        The type of trade to make when going in.
    exchange_pair : `ExchangePair`
        The exchange pair to perform the order for.
    price : float
        The current price.
    down_percent: float
        The percentage the price is allowed to drop before exiting.
    up_percent : float
        The percentage the price is allowed to rise before exiting.
    quantity : `Quantity`
        The quantity of the order.
    portfolio : `Portfolio`
        The portfolio being used in the order.
    start : int, optional
        The start time of the order.
    end : int, optional
        The end time of the order.

    Returns
    -------
    `Order`
        A stop order controlling for the percentages above and below the entry
        price.
    """

    side = TradeSide(side)
    instrument = side.instrument(exchange_pair.pair)

    if t_signal:
        order = Order(
            step=portfolio.clock.step,
            side=side,
            trade_type=TradeType(trade_type),
            exchange_pair=exchange_pair,
            quantity=quantity,
            portfolio=portfolio,
            price=price,
            t_signal=t_signal,
            start=start,
            end=end
        )
    else:
        order = Order_v1(
            step=portfolio.clock.step,
            side=side,
            trade_type=TradeType(trade_type),
            exchange_pair=exchange_pair,
            quantity=quantity,
            portfolio=portfolio,
            price_online=price,
            t_signal=t_signal,
            start=start,
            end=end
        )
    
    risk_criteria = Stop("down", down_percent, t_signal) ^ Stop("up", up_percent, t_signal)
    risk_management = OrderSpec(
        side=TradeSide.SELL if side == TradeSide.BUY else TradeSide.BUY,
        trade_type=TradeType.MARKET,
        exchange_pair=exchange_pair,
        t_signal=t_signal,
        criteria=risk_criteria
    )
    order.add_order_spec(risk_management)

    return order


def proportion_order(portfolio: 'Portfolio',
                     source: 'Wallet',
                     target: 'Wallet',
                     proportion: float,
                     t_signal: bool) -> 'Order':
    """Creates an order that sends a proportion of funds from one wallet to
    another.

    Parameters
    ----------
    portfolio : `Portfolio`
        The portfolio that contains both wallets.
    source : `Wallet`
        The source wallet for the funds.
    target : `Wallet`
        The target wallet for the funds.
    proportion : float
        The proportion of funds to send.
    """
    assert 0.0 < proportion <= 1.0
    exchange = source.exchange

    base_params = {
        'step': portfolio.clock.step,
        'portfolio': portfolio,
        'trade_type': TradeType.MARKET,
        'start': portfolio.clock.step,
        'end': portfolio.clock.step + 1
    }
    pair = None

    is_source_base = (source.instrument == portfolio.base_instrument)
    is_target_base = (target.instrument == portfolio.base_instrument)

    if t_signal:
        price = exchange_pair.price
    else:
        price = exchange_pair.price_online
            
    if is_source_base or is_target_base:
        if is_source_base:
            pair = source.instrument / target.instrument
        else:
            pair = target.instrument / source.instrument

        exchange_pair = ExchangePair(exchange, pair)

        balance = source.balance.as_float()
        size = min(balance * proportion, balance)
        quantity = (size * source.instrument).quantize()

        params = {
            **base_params,
            'side': TradeSide.BUY if is_source_base else TradeSide.SELL,
            'exchange_pair': exchange_pair,
            'quantity': quantity,
            'price': price,
            't_signal': t_signal
        }
        if t_signal:
            order = Order(
                **params
            )
        else:
            order = Order_v1(
                **params
            )
            
        return order

    pair = portfolio.base_instrument / source.instrument
    exchange_pair = ExchangePair(exchange, pair)

    balance = source.balance.as_float()
    size = min(balance * proportion, balance)
    quantity = (size * source.instrument).quantize()

    params = {
        **base_params,
        'side': TradeSide.SELL,
        'exchange_pair': exchange_pair,
        'quantity': quantity,
        'price': price,
        't_signal': t_signal
    }
    if t_signal:
        order = Order(
            **params
        )
    else:
        order = Order_v1(
            **params
        )
    order = Order(**params)

    pair = portfolio.base_instrument / target.instrument
    order.add_order_spec(OrderSpec(
        side=TradeSide.BUY,
        trade_type=TradeType.MARKET,
        exchange_pair=ExchangePair(exchange, pair),
        t_signal=t_signal,
        criteria=None
    ))
    return order
