import pyomo.environ as pyo

class EC__Residual_Load_MILP_model(): 
    def __init__(self, name='EC'):
        '''
        An Energy Community MILP Model.
        The parent pyomo model is required to have the following attributes:
        - model.timepoints : pyo.RangeSet, timepoints of the simulation
        - model.periods : pyo.RangeSet, eriods of the simulation
        - model.delta_t : pyo.Param, timedelta of the simulation
        
        Parameter:
        ---------
        name : str, name of the Energy Community model'''

        # Parameters
        self.name      = name

        # config info
        self.state_inputs     = [] # inputs to the state, needs to be a Parameter of the pyo.Block
        self.forcast_inputs   = ['P_resid_ec'] # inputs for forecast values, needs to be a Parameter of the pyo.Block with index model.periods
        self.controll_outputs = [] # outputs to the controller, needs to be a Variable of the pyo.Block with index model.periods
        self.shares           = ['P_el'] # connection to other variables (following egoistic sign logic, + is consumption, -is feedin) needs to be a pyo.Variable with index model.periods

    def pyo_block_rule(self, block):
        model = block.model()
        block.P_el       = pyo.Var(model.periods, domain=pyo.Reals) # Electrical Power in W (feed in = positive, consumption = negative)
        block.P_resid_ec = pyo.Param(model.periods, mutable=True, domain=pyo.Reals) # Residual load of EC (surplus_load > 0 > surplus_generation)

        # EC / Grid constraints:
        @block.Constraint(model.periods)
        def grid_constraint(b, p):
            return (b.P_el[p] == b.P_resid_ec[p]) 