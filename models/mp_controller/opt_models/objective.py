import pyomo.environ as pyo
from typing import Literal

class Objective(): 
    def __init__(self, name='EC', objective=Literal['self-consumption', 'self-consumption-slack', 'peak-power']):
        '''
        Objective function.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        name : str, name of the objective
        objective : Literal, objective function'''

        # Parameters
        self.name      = name

        # config info
        self.state_inputs     = [] # inputs to the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = [] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['P_el'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

        match objective:
            case 'self-consumption':
                self.pyo_block_rule = self._self_consumption_block_rule
            case 'self-consumption-slack':
                self.pyo_block_rule = self._self_consumption_block_rule_w_slack
                self.shares = ['P_el', 'slack']
            case 'peak-power':
                raise NotImplementedError('Not Yet Implemented')
            case _:
                raise ValueError(f"'{objective}' not a valid objective")

    def _self_consumption_block_rule(self, block):
        model = block.model()
        block.P_el          = pyo.Var(model.periods, domain=pyo.Reals) # Electrical Power in W (feed in = positive, consumption = negative)
        block.P_resid_plus  = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W 
        block.P_resid_minus = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W

        @block.Constraint(model.periods)
        def grid_constraint(b, p):
            return b.P_resid_plus[p] - b.P_resid_minus[p] == b.P_el[p]
        
        @block.Objective(sense=pyo.minimize)
        def objective_rule(b):
            return pyo.quicksum(b.P_resid_plus[p]+b.P_resid_minus[p] for p in model.periods)
        
    def _self_consumption_block_rule_w_slack(self, block):
        model = block.model()
        # Shared Variables
        block.P_el          = pyo.Var(model.periods, domain=pyo.Reals) # Electrical Power in W (feed in = positive, consumption = negative)
        block.slack         = pyo.Var(model.periods, domain=pyo.Reals) # Slack Variable in W
        
        # Helper Variables
        block.P_resid_plus  = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W 
        block.P_resid_minus = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W

        @block.Constraint(model.periods)
        def grid_constraint(b, p):
            return b.P_resid_plus[p] - b.P_resid_minus[p] == b.P_el[p]
        
        @block.Objective(sense=pyo.minimize)
        def objective_rule(b):
            return pyo.quicksum(b.P_resid_plus[p]+b.P_resid_minus[p] - block.slack[p] for p in model.periods)