import pyomo.environ as pyo

class BES_MILP_model():
    def __init__(self, name, E_min=0., E_max=20_000.*3600, P_max_cha=20_000., P_max_dis=20_000., eta_cha=0.95, eta_dis=0.95):
        '''
        A battery energy storag model with charging and discharging efficiencies.
        The model needs to be used in an parent model to function correctly!
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        E_min : float, minimum energy of the storage in J
        E_max : float, maximum energy of the storage in J
        P_max_cha : maximum charging power in W
        P_max_dis : maximum discharging powre in W
        eta_cha : float [0, 1] charging efficiency (no unit)
        eta_dis : float [0, 1] discharging efficiency (no unit)'''

        # Parameters
        self.name      = name
        self.E_min     = E_min # J
        self.E_max     = E_max # 20 kWh in J
        self.P_max_cha = P_max_cha # W
        self.P_max_dis = P_max_dis # W
        self.eta_cha   = eta_cha # 1
        self.eta_dis   = eta_dis # 1

        # config info
        self.state_inputs     = ['E_BES_0'] # inputs to the state, needs to be a Parameter of the pyo.Block
        self.states           = ['E']
        self.forcast_inputs   = [] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['P_el'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block):
        model = block.model()

        # Inputs
        block.E_BES_0   = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.E_min <= E and E <= self.E_max) # J

        # Variables / Outputs
        block.E         = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.E_min, self.E_max)) # J
        block.P_el      = pyo.Var(model.periods, domain=pyo.Reals) # Electrical Power in W (feed in = positive, consumption = negative)

        # helper Variables
        block.P_el_cha  = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Electrical charging Power in W (helper)
        block.P_el_dis  = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Electrical discharging Power in W (helper)
        block.bool      = pyo.Var(model.periods, domain=pyo.Boolean) # prevent same time charging and discharging

        @block.Constraint(model.periods)
        def energy_balance(block, p):
            return block.E[p+1] == block.E[p] + (block.P_el_cha[p] * self.eta_cha - block.P_el_dis[p] / self.eta_dis) * model.delta_t
        
        @block.Constraint(model.periods)
        def output_power(block, p):
            return block.P_el[p] == block.P_el_cha[p] - block.P_el_dis[p]

        @block.Constraint(model.periods)
        def power_limit_bool_cha(block, p):
            return block.P_el_cha[p] <= block.bool[p] * self.P_max_cha
        
        @block.Constraint(model.periods)
        def power_limit_bool_dis(block, p):
            return block.P_el_dis[p] <= block.bool[p] * self.P_max_dis

        @block.Constraint()
        def initial_condition(block):
            return block.E[0] == block.E_BES_0