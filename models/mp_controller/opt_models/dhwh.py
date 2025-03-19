import pyomo.environ as pyo

class DHW_MILP_model_Temp(): 
    def __init__(self, name, P_nom=2_000, C_tes=4200*200, T_tes_min=10, T_tes_max=80, eta=1):
        '''
        A domestic hot water heater with buffer storage MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        eta : float Coeficient of performance (fixed, no unit)
        P_nom : float, nominal electric power of the heating element in W
        E_tes_min : minimum storage capacity of the Thermal energy storage in J
        E_tes_max : maximum storage capacity of the Thermal energy storage in J'''

        # Parameters
        self.name      = name
        self.P_nom     = P_nom
        self.C_tes     = C_tes
        self.T_tes_min = T_tes_min
        self.T_tes_max = T_tes_max
        self.cop       = eta

        # config info
        self.state_inputs     = ['T_tes_0'] # inputs to initialize the state, needs to be a Parameter of the pyo.Block
        self.states           = ['T_tes']
        self.forcast_inputs   = ['dot_Q_demand'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['on'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block):
        model = block.model()

        # parameters that change for every run
        block.T_tes_0      = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.T_tes_min <= E and E <= self.T_tes_max) # J
        block.dot_Q_demand = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)

        # Variables
        block.T_tes     = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.T_tes_min, self.T_tes_max)) # J
        block.on        = pyo.Var(model.periods, domain=pyo.Boolean) # 0/1
        block.P_el      = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # W

        # Constraints
        # block.tes_e_limit_1 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.T_tes_min <= block.E_tes[t])
        # block.tes_e_limit_2 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.T_tes_max >= block.E_tes[t])

        @block.Constraint(model.periods)
        def dhwh_tes_constraint_energy_balance(block, p):
            return block.T_tes[p+1] == block.T_tes[p] + (block.P_el[p] * self.cop - block.dot_Q_demand[p]) * model.delta_t / self.C_tes
        
        block.tes_initial_condition = pyo.Constraint(rule=lambda block: block.T_tes[0] == block.T_tes_0)

        block.nominal_power         = pyo.Constraint(model.periods, rule=lambda block, p: block.P_el[p] == self.P_nom * block.on[p])


class DHW_MILP_model(): 
    def __init__(self, name, eta=1, P_nom=7_000, E_tes_min=200*4200*10, E_tes_max=200*4200*40):
        '''
        A domestic hot water heater with buffer storage MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        eta : float Coeficient of performance (fixed, no unit)
        P_nom : float, nominal electric power of the heating element in W
        E_tes_min : minimum storage capacity of the Thermal energy storage in J
        E_tes_max : maximum storage capacity of the Thermal energy storage in J'''

        # Parameters
        self.name      = name
        self.cop       = eta
        self.P_nom     = P_nom
        self.E_tes_min = E_tes_min
        self.E_tes_max = E_tes_max

        # config info
        self.state_inputs     = ['E_tes_0'] # inputs to initialize the state, needs to be a Parameter of the pyo.Block
        self.states           = ['E_tes']
        self.forcast_inputs   = ['dot_Q_demand'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['on'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block):
        model = block.model()

        # parameters that change for every run
        block.E_tes_0      = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.E_tes_min <= E and E <= self.E_tes_max) # J
        block.dot_Q_demand = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)

        # Variables
        block.E_tes     = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.E_tes_min, self.E_tes_max)) # J
        block.on        = pyo.Var(model.periods, domain=pyo.Boolean) # 0/1
        block.P_el      = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # W

        # Constraints
        # block.tes_e_limit_1 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.E_tes_min <= block.E_tes[t])
        # block.tes_e_limit_2 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.E_tes_max >= block.E_tes[t])

        @block.Constraint(model.periods)
        def dhwh_tes_constraint_energy_balance(block, p):
            return block.E_tes[p+1] == block.E_tes[p] + (block.P_el[p] * self.cop - block.dot_Q_demand[p]) * model.delta_t
        
        block.tes_initial_condition = pyo.Constraint(rule=lambda block: block.E_tes[0] == block.E_tes_0)

        block.nominal_power         = pyo.Constraint(model.periods, rule=lambda block, p: block.P_el[p] == self.P_nom * block.on[p])


class DHW_MILP_model_T_m(): 
    def __init__(self, name, P_nom=2_000, C_tes=4200*100, T_tes_min=10, T_tes_max=80, eta=1, T_out=50, T_in=12, c_p=4200):
        '''
        A domestic hot water heater with buffer storage MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        eta : float Coeficient of performance (fixed, no unit)
        P_nom : float, nominal electric power of the heating element in W
        C_tes : float, total thermal capacitance of the Thermal energy storage in J/K
        T_tes_min : float, minimum storage temperature of the Thermal energy storage in °C
        T_tes_max : float, maximum storage temperature of the Thermal energy storage in °C
        T_out : float, outlet water temperature in °C
        T_out : float, water inlet temperature in °C
        c_p : float, thermal capacitance of water in J/(kg K)'''

        # Parameters
        self.name        = name
        self.P_nom       = P_nom
        self.C_tes       = C_tes
        self.T_tes_min   = T_tes_min
        self.T_tes_max   = T_tes_max
        self.cop         = eta
        self.T_out       = T_out
        self.T_in        = T_in
        self.c_p         = c_p

        # config info
        self.state_inputs     = ['T_tes_0'] # inputs to initialize the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = ['dot_m_demand'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['on'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods
        self.states           = ['T_tes'] # state values

    def pyo_block_rule(self, block):
        model = block.model()
        # Inputs
        block.T_tes_0        = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.T_tes_min <= E and E <= self.T_tes_max) # J
        block.dot_m_demand   = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)

        # Shared Variables
        block.P_el           = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # W

        # Helper Variables
        block.dot_m_on       = pyo.Var(model.periods, domain=pyo.Reals, bounds=(0,1))
        block.dot_m_demand_h = pyo.Var(model.periods, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)
        block.T_tes     = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.T_tes_min, self.T_tes_max)) # J
        
        # Outputs
        block.on        = pyo.Var(model.periods, domain=pyo.Boolean) # 0/1

        # Constraints
        @block.Constraint(model.periods)
        def dhwh_tes_constraint_energy_balance(block, p):
            return block.T_tes[p+1] == block.T_tes[p] + (block.P_el[p] * self.cop - (block.dot_m_demand[p] * self.c_p * (block.T_tes[p] - self.T_in))) * model.delta_t / self.C_tes
        
        @block.Constraint(model.periods)
        def dhwh_tes_constraint(block, p):
            return block.dot_m_demand_h[p]  == block.dot_m_demand[p] * block.dot_m_on[p]

        @block.Constraint(model.periods)
        def dhwh_tes_constraint__(block, p):
            return block.dot_m_demand_h[p]  == block.dot_m_demand[p] 

        @block.Constraint(model.periods)
        def dhwh_tes_constraint_(block, p):
            return block.T_tes[p] >= self.T_out * block.dot_m_on[p]
 
        block.tes_initial_condition = pyo.Constraint(rule=lambda block: block.T_tes[0] == block.T_tes_0)

        block.nominal_power         = pyo.Constraint(model.periods, rule=lambda block, p: block.P_el[p] == self.P_nom * block.on[p])

class DHW_MILP_model_T_m_slack(): 
    def __init__(self, name, P_nom=2_000, C_tes=4200*100, T_tes_min=10, T_tes_max=80, eta=1, T_out=50, T_in=12, c_p=4200, slack_scale=1000):
        '''
        A domestic hot water heater with buffer storage MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        eta : float Coeficient of performance (fixed, no unit)
        P_nom : float, nominal electric power of the heating element in W
        C_tes : float, total thermal capacitance of the Thermal energy storage in J/K
        T_tes_min : float, minimum storage temperature of the Thermal energy storage in °C
        T_tes_max : float, maximum storage temperature of the Thermal energy storage in °C
        T_out : float, outlet water temperature in °C
        T_out : float, water inlet temperature in °C
        c_p : float, thermal capacitance of water in J/(kg K)
        slack_scale : float, scale for the slack variable in the temperature constraint in K/(objective_value (e.g. W))'''

        # Parameters
        self.name        = name
        self.P_nom       = P_nom
        self.C_tes       = C_tes
        self.T_tes_min   = T_tes_min
        self.T_tes_max   = T_tes_max
        self.cop         = eta
        self.T_out       = T_out
        self.T_in        = T_in
        self.c_p         = c_p
        self.slack_scale = slack_scale

        # config info
        self.state_inputs     = ['T_tes_0'] # inputs to initialize the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = ['dot_m_demand'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['on', 'slack'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el', 'slack'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods
        self.states           = ['T_tes'] # state values

    def pyo_block_rule(self, block):
        model = block.model()
        # Inputs
        block.T_tes_0        = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.T_tes_min <= E and E <= self.T_tes_max) # J
        block.dot_m_demand   = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)
        block.is_demand      = pyo.Param(model.periods, mutable=True, domain=pyo.Boolean) # Demand > 0

        # Shared Variables
        block.P_el           = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # W
        block.slack          = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # Objective value

        # Helper Variables
        block.dot_m_on       = pyo.Var(model.periods, domain=pyo.Reals, bounds=(0,1))
        block.dot_m_demand_h = pyo.Var(model.periods, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)
        block.T_tes          = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.T_tes_min, self.T_tes_max)) # J
        
        # Outputs
        block.on        = pyo.Var(model.periods, domain=pyo.Boolean) # 0/1

        # Constraints
        @block.Constraint(model.periods)
        def dhwh_tes_constraint_energy_balance(block, p):
            return block.T_tes[p+1] == block.T_tes[p] + (block.P_el[p] * self.cop - (block.dot_m_demand[p] * self.c_p * (block.T_tes[p] - self.T_in))) * model.delta_t / self.C_tes
        
        @block.Constraint(model.periods)
        def dhwh_tes_constraint(block, p):
            return block.dot_m_demand_h[p]  == block.dot_m_demand[p] * block.dot_m_on[p]

        @block.Constraint(model.periods)
        def dhwh_tes_constraint__(block, p):
            return block.dot_m_demand_h[p]  == block.dot_m_demand[p] 

        @block.Constraint(model.periods)
        def dhwh_tes_constraint_(block, p):
            return block.T_tes[p] >= self.T_out * block.dot_m_on[p] - block.slack[p]*self.slack_scale
 
        block.tes_initial_condition = pyo.Constraint(rule=lambda block: block.T_tes[0] == block.T_tes_0)

        block.nominal_power         = pyo.Constraint(model.periods, rule=lambda block, p: block.P_el[p] == self.P_nom * block.on[p])


class DHW_MILP_model_E_m(): 
    def __init__(self, name, eta=1, P_nom=7_000, E_tes_min=200*4200*10, E_tes_max=200*4200*40):
        '''
        A domestic hot water heater with buffer storage MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        eta : float Coeficient of performance (fixed, no unit)
        P_nom : float, nominal electric power of the heating element in W
        E_tes_min : minimum storage capacity of the Thermal energy storage in J
        E_tes_max : maximum storage capacity of the Thermal energy storage in J'''

        # Parameters
        self.name      = name
        self.cop       = eta
        self.P_nom     = P_nom
        self.E_tes_min = E_tes_min
        self.E_tes_max = E_tes_max

        # config info
        self.state_inputs     = ['E_tes_0'] # inputs to initialize the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = ['dot_Q_demand'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = ['on'] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block):
        model = block.model()

        # parameters that change for every run
        block.E_tes_0      = pyo.Param(mutable=True, domain=pyo.NonNegativeReals, validate=lambda _, E: self.E_tes_min <= E and E <= self.E_tes_max) # J
        block.dot_Q_demand = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Consumed Energy from storage in W (consumption < 0 < heat gain)

        # Variables
        block.E_tes     = pyo.Var(model.timepoints, domain=pyo.NonNegativeReals, bounds=(self.E_tes_min, self.E_tes_max)) # J
        block.on        = pyo.Var(model.periods, domain=pyo.Boolean) # 0/1
        block.P_el      = pyo.Var(model.periods, domain=pyo.NonNegativeReals) # W

        # Constraints
        # block.tes_e_limit_1 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.E_tes_min <= block.E_tes[t])
        # block.tes_e_limit_2 = pyo.Constraint(m.timepoints, rule=lambda block, t: self.E_tes_max >= block.E_tes[t])

        @block.Constraint(model.periods)
        def dhwh_tes_constraint_energy_balance(block, p):
            return block.E_tes[p+1] == block.E_tes[p] + (block.P_el[p] * self.cop - block.dot_Q_demand[p]) * model.delta_t
        
        block.tes_initial_condition = pyo.Constraint(rule=lambda block: block.E_tes[0] == block.E_tes_0)

        block.nominal_power         = pyo.Constraint(model.periods, rule=lambda block, p: block.P_el[p] == self.P_nom * block.on[p])

