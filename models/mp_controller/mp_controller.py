import pyomo.environ as pyo
from .forcasting import ForcastingProto
from .opt_models.MILP_model_proto import MILPModelProto
from pyomo.contrib.appsi.solvers.highs import Highs
from pyomo.contrib.appsi.solvers.gurobi import Gurobi


class MPController():
    def __init__(self, name, n_periods, delta_t, pyo_solver_name='appsi_highs', sep='.', return_forcast=False, return_future_control_output=False, return_future_state=False):
        '''A model predicteve Controller utilizing MILP with pyomo. 
        MILP Models can be added to the model via the add_model() method. Added models need to follow a given structure. 
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
        
        self.shared_vars = set()

        self.sep = sep

        self.return_forcast = return_forcast
        self.return_future_state = return_future_state
        self.return_future_control_output = return_future_control_output

        # self.solver = Highs() # 
        self.solver = pyo.SolverFactory(pyo_solver_name)
        # self.solver = Gurobi()

        # make Energy Community model
        self.model      = pyo.ConcreteModel()

        self.model.timepoints = pyo.RangeSet(0, n_periods) # Range of timepoints
        self.model.periods    = pyo.RangeSet(0, n_periods-1) # Range of periods
        self.model.delta_t    = pyo.Param(initialize=delta_t) # s

        self.components = [] # list of components that get added via add_model (they need to follow a specific syntax! see examples)
        self.forcasters = [] # list of forcasters that get added via add_model (they need to follow a specific syntax! see examples)    

    def add_model(self, component:MILPModelProto):
        '''add a model which needs to follow the given structure, see the examples'''
        # add components to the list of components
        self.components += [component]
        # Add constraints as a block to the EC model:
        self.model.add_component(component.name, pyo.Block(rule=component.pyo_block_rule))

        # append model inputs, outputs and shared values 
        self.inputs += [component.name+self.sep+si for si in component.state_inputs]
        self.outputs += [component.name+self.sep+o for o in component.controll_outputs]

        for shared in component.shares:
            if shared not in self.shared_vars:
                # Add expression and Constraint for shared variable to the model
                self.shared_vars.add(shared)
                self.model.add_component('sum_expr_'+shared, pyo.Expression(self.model.periods, rule=0))
                rule = lambda m, p: m.find_component('sum_expr_'+shared)[p] == 0
                self.model.add_component('sum_constraint_'+shared, 
                                         pyo.Constraint(self.model.periods, rule=rule))
            # Add the shared variable to the corresponding Expression
            comp = self.model.find_component(component.name)
            shared_attr = comp.find_component(shared)
            for p in self.model.periods:
                self.model.find_component('sum_expr_'+shared)[p] += shared_attr[p]

        # modify output
        if self.return_future_control_output:
            self.outputs += [component.name+self.sep+out_name+'_future' for out_name in component.controll_outputs]

        if self.return_future_state:
            if hasattr(component, 'states'):
                self.outputs += [component.name+self.sep+state+'_future' for state in component.states]

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
        
        # forecaster name prefix
        pre = for_model.name + self.sep + 'forecast' + self.sep
        complete_for_var = pre+for_var

        # add forecast input to general inputs
        for inp in forcaster.inputs:
            self.inputs += [pre+inp]
        
        self.forcasters += [(pre, for_var, forcaster)]

        forcaster.set_forcast_length(self.n_periods)
        if hasattr(forcaster, 'set_delta_t'):
            forcaster.set_delta_t(self.delta_t)

        # modify outputs
        if self.return_forcast:
            self.outputs += [complete_for_var]

    def step(self, time, **inputs):      
        # update forecasters with input data
        for pre, _, forecaster in self.forcasters:
            # map inputs for forcasters
            forc_inputs = {inp: inputs[pre+inp] for inp in forecaster.inputs}
            forecaster.set_data(time, **forc_inputs)

        # create forecasts
        forecasts = {}
        for pre, for_var, forecaster in self.forcasters:
            forecasts[pre+for_var] = forecaster.get_forcast(time)

        # initialize component states
        for comp in self.components:
            for state_name in comp.state_inputs:
                self.model.find_component(comp.name).__setattr__(state_name, inputs[comp.name+self.sep+state_name])

        # initialize component with forecasts
        for comp in self.components:
            opt_comp = self.model.find_component(comp.name)
            for for_var in comp.forcast_inputs:
                opt_forc_attr = opt_comp.__getattribute__(for_var)
                
                pre = comp.name + self.sep + 'forecast' + self.sep
                forec_values = forecasts[pre+for_var]

                for p in self.model.periods:
                    opt_forc_attr.__setitem__(p, forec_values[p])

        self.model.pprint()
        solver_outpt = self.solver.solve(self.model, tee=True)

        # get outputs from models
        outputs = {}
        for comp in self.components:
            pyo_comp = self.model.find_component(comp.name)
            for out_name in comp.controll_outputs:
                outputs[comp.name+self.sep+out_name] = pyo.value(pyo_comp.__getattribute__(out_name)[0])
                # outputs[out_name+'_of_'+comp.name] = pyo.value(pyo_comp.__getattribute__(out_name)[0])

        if self.return_forcast:
            outputs.update(forecasts)

        if self.return_future_control_output: 
            for comp in self.components:
                pyo_comp = self.model.find_component(comp.name)
                for out_name in comp.controll_outputs:
                    # outputs[out_name+'_of_'+comp.name+ '_future'] = [pyo.value(pyo_comp.__getattribute__(out_name)[i]) for i in self.model.periods]
                    outputs[comp.name+self.sep+out_name+'_future'] = [pyo.value(pyo_comp.__getattribute__(out_name)[i]) for i in self.model.periods]

        if self.return_future_state:
            for comp in self.components:
                pyo_comp = self.model.find_component(comp.name)
                if hasattr(comp, 'states'):
                    for states in comp.states:
                        outputs[comp.name+self.sep+states+'_future'] = [pyo.value(pyo_comp.__getattribute__(states)[i]) for i in self.model.timepoints]
                        # outputs[states+'_of_'+comp.name + '_future'] = [pyo.value(pyo_comp.__getattribute__(states)[i]) for i in self.model.timepoints]

        return outputs
    
