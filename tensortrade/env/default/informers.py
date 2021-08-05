
from tensortrade.env.generic import Informer, TradingEnv, TradingEnv_v1


class TensorTradeInformer(Informer):

    def __init__(self) -> None:
        super().__init__()

    def info(self, env: 'TradingEnv_v1') -> dict:
        return {
            'step': self.clock.step,
            'net_worth': env.action_scheme.portfolio.net_worth
        }
    

class TensorTradeInformer_v1(Informer):
    print("44444444444444444444444444444444444444444444444444444444444")

    def __init__(self) -> None:
        super().__init__()

    def info(self, env: 'TradingEnv_v1') -> dict:
        print("55555555555555555555555555555555555555555555555555555555555")
        return {
            'step': self.clock.step,
            'net_worth': env.action_scheme.portfolio.net_worth
        }
