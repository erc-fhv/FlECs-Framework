import pandas as pd
import datetime

from simplec import Simulation
from simplec_examples import 

# Models
from models.demand.loadprofilegenerator import Household
from models.electricity_grid.electricity_grid_simple import Grid
from models.smart_meter.smart_meter import SmartMeter
from models.battery_storage.battery_storage import BatteryStorage
from models.pv.pv import PvgisPV
from models.TES.DHWH import TESModel

# Controller
from models.mp_controller.mp_controller import MPController
from models.mp_controller.opt_models.battery_storage import BES_MILP_model
from models.mp_controller.opt_models.energy_community import Residual_Load_MILP_model
from models.mp_controller.forcasting import Forcasting
from models.mp_controller.opt_models.dhwh_dot_m import DHW_MILP_model_Temp


sim = Simulation(output_data_path=f'output/tutorial_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.csv')

# Grid
grid = Grid('grid')
sim.add_model(grid, watch_values=['P_substation'])

# Smart meter
sm = SmartMeter(name='sm')
sim.add_model(sm)
sim.connect(sm, grid, ('P_grid', 'P_'))

# PV
pv = PvgisPV('pv', peakpower=2_000)
sim.add_model(pv, watch_values=['P_pv'])
sim.connect(pv, sm, ('P_pv', 'P_'))

# Household Loads
household = Household(
    name='household',
    lpg_dir='data/loadprofilegenerator/CHR41 Family with 3 children, both at work/Results'
    )
sim.add_model(household, watch_values=['P_el', 'dot_m_ww'])
sim.connect(household, sm, ('P_el', 'P_'))

# DHWH
dhwh = TESModel(name='dhwh', delta_t=60, P_el_nom=3_600, V=0.1, N=10, P_el_nom=2_000)
sim.add_model(dhwh, watch_values=['T_tw','T_0'])

sim.connect(household, dhwh, ('dot_m_ww', 'dot_m_o_DHW'))
sim.connect(dhwh, sm, ('P_el', 'P_'))
sim.connect_constant(21, dhwh, 'T_inf')
sim.connect_constant(12, dhwh, 'T_i_DHW')

# Battery Storage
bes = BatteryStorage(
    name = 'bes',
    delta_t             = 60*60,
    E_max               = 2_000*3600, # J
    E_0                 = 1_000*3600, # J
    P_max_charge        = 2_000, # W
    P_max_discharge     = 2_000, # W
)
sim.add_model(bes, watch_values=['P_set', 'P_grid', 'E'])
sim.connect(bes, sm, ('P_grid', 'P_'))


#######################
# Controller Setup
#######################
mp_contr = MPController(name='MPC', n_periods=24, delta_t=3600)

## Model of household
milp_resid_load  = Residual_Load_MILP_model()
mp_contr.add_model(milp_resid_load)

## Forcast for household
ec_forcast = Forcasting('generic_single_var_persistence', default_val=0)  ## TODO
mp_contr.add_forcaster(ec_forcast, milp_resid_load, 'P_resid')

# BES
milp_bes = BES_MILP_model(  # TODO Check params
    name='bes',
    E_min=0,
    E_max=20_000*3600, # J
    P_max_cha=20000, # W
    P_max_dis=20000, # W
    eta_cha=0.9, # 
    eta_dis=0.9 # 
    )

mp_contr.add_model(milp_bes)

# DHWH 1
milp_dhwh = DHW_MILP_model_Temp(name='dhwh1', P_nom=3600, C_tes=4200*100)
mp_contr.add_model(milp_dhwh)

## Forcast for temperature in DHWH 1
milp_dhwh_forcast = Forcasting('generic_single_var_persistence','dot_m_demand', init_val=0)

mp_contr.add_forcaster(milp_dhwh_forcast, milp_dhwh, 'dot_m_demand')


# connect controller to the models
sim.add_model(mp_contr, watch_values=['E_BES_0_of_bes', 'P_el_of_bes','on_of_dhwh1']) 


sim.connect(bes, mp_contr, ('E', 'E_BES_0_of_bes'), ('P_grid', 'P_flex_'))

sim.connect(mp_contr, battery_storage, ('P_el_of_bes', 'P_set'), time_shifted=True, init_values={'P_el_of_bes': 0})

sim.connect(dhwh_appartment1, mp_contr,  ('T_tw', 'T_tes_0_of_dhwh1'))

sim.connect(appartment1, mp_contr, ('dot_m_ww','dot_m_demand'))

sim.connect(mp_contr, dhwh_appartment1, ('on_of_dhwh1', 'state'), time_shifted=True, init_values={'on_of_dhwh1': 0})

# sim.connect(dhwh_appartment2, mp_contr,  ('T_tw', 'T_tes_0_of_dhwh2'))

# sim.connect(appartment2, mp_contr, ('dot_m_ww','dot_m_demand'))

# sim.connect(mp_contr, dhwh_appartment2, ('on_of_dhwh2', 'state'), time_shifted=True, init_values={'on_of_dhwh2': 0})

# times = pd.date_range('2021-01-01 00:00:00', '2021-01-01 23:59:00', freq='1min', tz='Europe/Berlin')
# times = pd.date_range('2021-01-01 00:00:00', '2021-12-31 23:59:00', freq='1min', tz='Europe/Berlin')
#times = pd.date_range('2021-01-01 00:00:00', '2021-01-07 00:00:00', freq='1min', tz='Europe/Berlin')
times = pd.date_range('2021-07-01 00:00:00', '2021-07-07 00:00:00', freq='1min', tz='Europe/Berlin')
# sim.draw_exec_graph()

# sim.run(times)
cProfile.run('sim.run(times)', f'temp/restats_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.prof')
