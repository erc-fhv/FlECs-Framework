from models.mp_controller.mp_controller import MPController
from models.mp_controller.opt_models.battery_storage import BES_MILP_model
from models.mp_controller.opt_models.energy_community import EC__Residual_Load_MILP_model
from models.mp_controller.forcasting import Forcasting
import pyomo.environ as pyo

def test_MPController_init():
    mpc = MPController(3, 60*15)

    assert isinstance(mpc.model, pyo.ConcreteModel)
    assert isinstance(mpc.model.periods, pyo.RangeSet)
    assert isinstance(mpc.model.timepoints, pyo.RangeSet)
    assert isinstance(mpc.model.delta_t, pyo.Param)

def test_MPController_add_model():
    class ComponentMock():
        name = 'comp'
        state_inputs = ['a']
        shares = ['P_el']
        def pyo_block_rule(self, block):
            block.P_el = pyo.Var(block.model().periods)
    
    mpc = MPController(3, 60*15)
    cm = ComponentMock()
    mpc.add_model(cm)

    assert cm in mpc.components
    assert hasattr(mpc.model, 'comp')
    assert isinstance(mpc.model.comp, pyo.Block)
    assert 'a_of_comp' in mpc.inputs

def test_simple_scenario():
    ctr = MPController(n_periods=3,
                       delta_t=1)
    # EC
    ec = EC__Residual_Load_MILP_model()
    ctr.add_model(ec)

    class ForcastingMock():
        def __init__(self, inputs):
            self.inputs = inputs

        def get_forcast(self) -> list:
            return [1, 0, 0]

        def set_data(self):
            pass
        
        def set_forcast_length(self, n):
            pass

    ec_fc = ForcastingMock([])
    ctr.add_forcaster(ec_fc, ec, 'P_resid_ec')

    # BES
    bes = BES_MILP_model('BES', 
                         E_min=0, 
                         E_max=5,
                         P_max_cha=1,
                         P_max_dis=1,
                         eta_cha=1,
                         eta_dis=1)
    ctr.add_model(bes)

    outputs = ctr.step(1, E_BES_0_of_BES=2)

    assert 'P_el_of_BES' in outputs
    assert outputs['P_el_of_BES'] == -1.

def test_forcaster_integration():
    ctr = MPController(n_periods=3,
                       delta_t=1)
    # EC
    ec = EC__Residual_Load_MILP_model()
    ctr.add_model(ec)

    class ForcastingMock():
        def __init__(self):
            self.inputs = ['data']
            self.data = []

        def get_forcast(self) -> list:
            return self.data

        def set_data(self, data):
            assert len(data) == self.n_periods
            self.data = data
        
        def set_forcast_length(self, n):
            self.n_periods = n

    ec_fc = ForcastingMock()
    ctr.add_forcaster(ec_fc, ec, 'P_resid_ec')

    # BES
    bes = BES_MILP_model('BES', 
                         E_min=0, 
                         E_max=5,
                         P_max_cha=1,
                         P_max_dis=1,
                         eta_cha=1,
                         eta_dis=1)
    ctr.add_model(bes)

    outputs = ctr.step(1, E_BES_0_of_BES=2, data=[1, 0, 0])

    assert outputs['P_el_of_BES'] == -1.


def test_complete_scenario():
    ctr = MPController(n_periods=3,
                       delta_t=1)
    # EC
    ec = EC__Residual_Load_MILP_model()
    ctr.add_model(ec)

    ec_fc = Forcasting(
        method='generic_single_var_persistence',
        inpt='P_ec',
        delay=1,
        init_val=0)
    
    ctr.add_forcaster(ec_fc, ec, 'P_resid_ec')

    # BES
    bes = BES_MILP_model('BES', 
                         E_min=0, 
                         E_max=5,
                         P_max_cha=1,
                         P_max_dis=1,
                         eta_cha=1,
                         eta_dis=1)
    ctr.add_model(bes)

    outputs = ctr.step(1, E_BES_0_of_BES=2, P_ec=1)
    assert outputs['P_el_of_BES'] == 0.

    outputs = ctr.step(2, E_BES_0_of_BES=2, P_ec=1)
    assert outputs['P_el_of_BES'] == 0.

    outputs = ctr.step(3, E_BES_0_of_BES=2, P_ec=1)
    assert outputs['P_el_of_BES'] == 0.

    outputs = ctr.step(4, E_BES_0_of_BES=2, P_ec=1)
    assert outputs['P_el_of_BES'] == -1.

    outputs = ctr.step(5, E_BES_0_of_BES=1, P_ec=1)
    assert outputs['P_el_of_BES'] == -1.

    outputs = ctr.step(5, E_BES_0_of_BES=0, P_ec=1)
    assert outputs['P_el_of_BES'] == 0.

