import pyomo.environ as pyo
from .forcasting import ForcastingProto
from .opt_models.MILP_model_proto import MILPModelProto

class MPController():
    def __init__(self, name, n_periods, delta_t, pyo_solver_name='appsi_highs', return_forcast=False):
        '''A model predicteve Controller utilizing MILP with pyomo. 
        MILP Models can be added to the model via the add_model() method. Added modles need to follow a given structure. 
        Please find examples for reference.
        Inputs and outputs get configured automatically based on the added models.
        
        Parameters
        ----------
        n_periods : int, length of optimization horizon
        delta_t : int, timedelta of the controller in s
        pyo_solver_name : str, name of a pyomo solver (passed to pyo.SolverFactory)
        return_forcast : bool, return the forcast values as outputs of the controller model
        '''
        self.name       = name
        self.n_periods  = n_periods
        self.delta_t    = delta_t
        self.inputs = []
        self.outputs = []

        self.return_forcast = return_forcast

        self.solver = pyo.SolverFactory(pyo_solver_name)

        # make Energy Community model
        self.model      = pyo.ConcreteModel()

        self.model.timepoints = pyo.RangeSet(0, n_periods) # Range of timepoints
        self.model.periods    = pyo.RangeSet(0, n_periods-1) # Range of periods
        self.model.delta_t    = pyo.Param(initialize=delta_t) # s

        self.model.P_resid_plus  = pyo.Var(self.model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W 
        self.model.P_resid_minus = pyo.Var(self.model.periods, domain=pyo.NonNegativeReals) # Residual Grid load W

        self.components = [] # list of components that get added via add_model (they need to follow a specific syntax! see examples)
        self.forcasters = [] # list of forcasters that get added via add_model (they need to follow a specific syntax! see examples)    

        # Grid constraints:
        # TODO: this could be made generic by summing over all 'shared' values of the models
        # This expresisions get extended in the add model method, by the P_el of the components
        @self.model.Expression(self.model.periods)
        def grid_expression(m, p):
            return m.P_resid_plus[p] - m.P_resid_minus[p]
        
        @self.model.Constraint(self.model.periods)
        def grid_constraint(m, p):
            return self.model.grid_expression[p] == 0 

        # TODO: this could be made parametric / object oriented / made a component
        @self.model.Objective(sense=pyo.minimize)
        def objective_rule(m):
            return pyo.quicksum(m.P_resid_plus[p]+m.P_resid_minus[p] for p in m.periods)

    def add_model(self, component:MILPModelProto):
        '''add a model which needs to follow the given structure, see the examples'''
        # add components to the list of components
        self.components += [component]
        # Add constraints as a block to the EC model:
        self.model.__setattr__(component.name, pyo.Block(rule=component.pyo_block_rule))
        # append model inputs, outputs and shared values 
        self.inputs += [si+'_of_'+component.name for si in component.state_inputs]
        self.outputs += [o+'_of_'+component.name for o in component.controll_outputs]

        # add the models P_el to the grid constraint (so the model does not need to be updated later)
        if 'P_el' in component.shares:
            comp = self.model.find_component(component.name)
            for p in self.model.periods:
                self.model.grid_expression[p] += comp.P_el[p]

    def add_forcaster(self, forcaster:ForcastingProto, for_model:MILPModelProto, for_var:str):
        '''Adds a forcasting objct to the controller for a model input of the MILP model
        Parameters
        ----------
        forcaster :  Forcast, forcsting object for a variable 
        for_model : MILP_Model, the model that the forcast is for
        for_vars : str, the forcast_inputs attribute of for_model to connect the forcast to'''
        if for_model not in self.components:
            raise ValueError(f'Model "{for_model.name}" needs to be added to the controller before the forcaster can be assigned')
        if for_var not in for_model.forcast_inputs: 
            raise AttributeError(f'Model {for_model} has no forcast input {for_var}')
        
        # add forecast input to general inputs
        for inp in forcaster.inputs:
            if inp not in self.inputs:
                self.inputs += [inp]

        complete_for_vars =[for_var+'_of_'+for_model.name]
        self.forcasters += [(complete_for_vars, forcaster)]

        forcaster.set_forcast_length(self.n_periods)
        if hasattr(forcaster, 'set_detla_t'):
            forcaster.set_delta_t(self.delta_t)

        if self.return_forcast:
            self.outputs += complete_for_vars

    def step(self, time, **inputs):
        # TODO: create observers to manipulate the input variables

        # initialize component states
        for comp in self.components:
            for state_name in comp.state_inputs:
                self.model.find_component(comp.name).__setattr__(state_name, inputs[state_name+'_of_'+comp.name])
        
        # update forcasters with input data
        for _, forc in self.forcasters:
            # get inputs for forcasters
            forc_inputs = {k: inputs[k] for k in forc.inputs}
            forc.set_data(time, **forc_inputs)

        # create forcasts
        forcast_outputs = {}
        for for_vars, forc in self.forcasters:
            forc_out = forc.get_forcast(time)
            outputs_maped = {k: forc_out for k in for_vars}
            forcast_outputs.update(outputs_maped)

        # initialize component forcasts  # UFF!!! TODO simplify!
        for comp in self.components:
            for forc_name in comp.forcast_inputs:
                comp = self.model.find_component(comp.name)
                name = forc_name+'_of_'+comp.name
                for p in self.model.periods:
                    comp.__getattribute__(forc_name).__setitem__(p, forcast_outputs[name][p])

        self.solver.solve(self.model)

        # get outputs from models
        outputs = {}
        for comp in self.components:
            pyo_comp = self.model.find_component(comp.name)
            for out_name in comp.controll_outputs:
                outputs[out_name+'_of_'+comp.name] = pyo.value(pyo_comp.__getattribute__(out_name)[0])

        if self.return_forcast:
            outputs.update(forcast_outputs)

        return outputs
    
