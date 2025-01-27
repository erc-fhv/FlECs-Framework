import pyomo.environ as pyo
from typing import Protocol, runtime_checkable

@runtime_checkable
class MILPModelProto(Protocol):
    def __init__(self, name:str):
        # Parameters
        self.name      = name

        # config info
        self.state_inputs     = [] # inputs to the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = [] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = [] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = [] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block:pyo.Block) -> None:
        model = block.model()