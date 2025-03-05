import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import cProfile

from simplec import Simulation

# Models
from models.building.building import BuildingModel
from models.heat_pump.heat_pump import HeatPumpEventBased, HeatPumpWControlEventBased, HeatPumpCoolingcircleWControl
from models.hysteresis_controller.hysteresis_controller import HystController
from models.weather.weather import SynproWeather
from models.demand.loadprofilegenerator import Household
from models.smart_meter.smart_meter import SmartMeter
from models.electricity_grid.electricity_grid_simple import Grid
from models.gridoperator.gridoperator import GridOperator
from models.battery_storage.battery_storage import BatteryStorage
from models.pv.pv import SynproPV
from models.TES.DHWH import TESModel

# Controller
from models.mp_controller.mp_controller import MPController
from models.mp_controller.opt_models.battery_storage import BES_MILP_model
from models.mp_controller.opt_models.energy_community import EC__Residual_Load_MILP_model
from models.mp_controller.forcasting import Forcasting
from models.mp_controller.opt_models.dhwh_dot_m import DHW_MILP_model_Temp


sim = Simulation(output_data_path=f'output/output_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.csv')

# Weather
weather    = SynproWeather(name='weather')
sim.add_model(weather,    watch_values=['T_amb', 'I_dir', 'I_dif'])

# Grid
grid = Grid('grid')
sim.add_model(grid, watch_values=['P_substation'])

# Gridoperator
gridoperator = GridOperator(name='grid_operator')
sim.add_model(gridoperator) # , watch_values=['df_P_day'])

###########
# Building
###########
# Building Envelope
building   = BuildingModel(name='building_envelope', count_of_dot_Q_int=2)
sim.add_model(building,   watch_values=['T_building'])
sim.connect(weather, building, 'T_amb', 'I_dir', 'I_dif', 'I_s', 'I_w', 'I_n', 'I_e')
sim.connect_constant(0.0, building, 'dot_Q_cool')

pv = SynproPV('pv', 20_000)  #  TODO: Replace PV model!
sim.add_model(pv, watch_values=['P_pv'])

# Heat Pump
# heatpump   = HeatPumpWControlEventBased(
#     'heatpump',
#     eta=0.4,
#     dot_Q_hp_nom=15000,
#     P_el_max=4000,
#     P_el_min=1000
#     )
heatpump = HeatPumpCoolingcircleWControl(
    'heatpump',
    P_el_max=4000
    )
sim.add_model(heatpump,   watch_values=['P_el', 'dot_Q_hp'])
sim.connect(heatpump, building, ('dot_Q_hp', 'dot_Q_heat'))
sim.connect(weather, heatpump, ('T_amb', 'T_source'))
sim.connect(building, heatpump, ('T_building', 'T_sink'), time_shifted=True, init_values={'T_building': 21})

# HP Controller
controller = HystController(
    'controller',
    hyst=2.
    )
sim.add_model(controller)
sim.connect(controller, heatpump, ('state', 'state'), triggers=['state'])
sim.connect(building, controller, ('T_building', 'T_is'), time_shifted=True, init_values={'T_building': 21})

# Battery storage
battery_storage = BatteryStorage(
    name = 'battery_storage_1',
    E_max               = 20000*3600, # J
    E_min               = 0*3600, # J
    E_0                 = 10000*3600, # J
    P_max_charge        = 20000, # W
    P_max_discharge     = 20000, # W
    eta_charge          = 0.9,
    eta_discharge       = 0.9,
    self_discharge_rate = 0, # 1/s
    delta_t             = 60*15,
)
sim.add_model(battery_storage, watch_values=['P_set', 'P_grid', 'E'])
# sim.connect_constant(2000, battery_storage, 'P_set') # Mock controller

# Smart meter
smartmeter_building = SmartMeter(name='smartmeter_building')
sim.add_model(smartmeter_building)
sim.connect(pv, smartmeter_building, ('P_pv', 'P_'))
sim.connect(heatpump, smartmeter_building, ('P_el', 'P_'))
sim.connect(battery_storage, smartmeter_building, ('P_grid', 'P_'))
sim.connect(smartmeter_building, grid, ('P_grid', 'P_'))
gridoperator.register_smartmeter(smartmeter_building)
sim.connect_nothing(smartmeter_building, gridoperator)

##############
# Appartments
##############

###############
# Appartment 1
###############
appartment1 = Household(
    name='appartment_1',
    lpg_dir='data/loadprofilegenerator/CHR41 Family with 3 children, both at work/Results'
    )
sim.add_model(appartment1, 
              watch_values=['P_el', 'dot_m_ww', 'dot_Q_gain_int']
              )
sim.connect(appartment1, building, ('dot_Q_gain_int', 'dot_Q_int_0'))

# Smart meter
smartmeter_apprtmnt1 = SmartMeter(name='smartmeter_appartment_1')
sim.add_model(smartmeter_apprtmnt1)
sim.connect(appartment1, smartmeter_apprtmnt1, ('P_el', 'P_'))
sim.connect(smartmeter_apprtmnt1, grid, ('P_grid', 'P_'))
gridoperator.register_smartmeter(smartmeter_apprtmnt1)
sim.connect_nothing(smartmeter_apprtmnt1, gridoperator)

# DHWH
dhwh_appartment1 = TESModel(name='appartment_1_dhwh', delta_t=60, T0=[80., 80., 80., 80., 80., 80., 80., 80., 80., 80.], P_el_nom=3600, V=0.1)
sim.add_model(dhwh_appartment1, watch_values=['T_tw','T_0'])
sim.connect(appartment1, dhwh_appartment1, ('dot_m_ww', 'dot_m_o_DHW'))
sim.connect(building, dhwh_appartment1, ('T_building', 'T_inf'))
sim.connect_constant(12, dhwh_appartment1, 'T_i_DHW')

###############
# Appartment 2   # TODO: create and change profile
###############
appartment2 = Household(
    name='appartment_2',
    lpg_dir='data/loadprofilegenerator/CHR41 Family with 3 children, both at work/Results'
    )
sim.add_model(appartment2, 
              watch_values=['P_el', 'dot_m_ww', 'dot_Q_gain_int']
              )
sim.connect(appartment2, building, ('dot_Q_gain_int', 'dot_Q_int_1'))

# Smart meter
smartmeter_apprtmnt2 = SmartMeter(name='smartmeter_appartment_2')
sim.add_model(smartmeter_apprtmnt2)
sim.connect(appartment2, smartmeter_apprtmnt2, ('P_el', 'P_'))
sim.connect(smartmeter_apprtmnt2, grid, ('P_grid', 'P_'))
gridoperator.register_smartmeter(smartmeter_apprtmnt2)
sim.connect_nothing(smartmeter_apprtmnt2, gridoperator)

# # DHWH
# dhwh_appartment2 = TESModel(name='appartment_2_dhwh', delta_t=60, T0=[80., 80., 80., 80., 80., 80., 80., 80., 80., 80.], P_el_nom=3600, V=0.1)
# sim.add_model(dhwh_appartment2, watch_values=['T_tw','T_0'])
# sim.connect(appartment2, dhwh_appartment2, ('dot_m_ww', 'dot_m_o_DHW'))
# sim.connect(building, dhwh_appartment2, ('T_building', 'T_inf'))
# sim.connect_constant(12, dhwh_appartment2, 'T_i_DHW')


#######################
# Controller Setup
#######################
mp_contr = MPController(name='MPC', n_periods=48, delta_t=60*15, return_forcast=True)

############
# EC
############
## Model of EC
milp_ec  = EC__Residual_Load_MILP_model()
mp_contr.add_model(milp_ec)

## Forcast for EC
ec_forcast = Forcasting('persistence_residual_load_smartmeter', default_val=0)
# register ec forcast at gridoperator, to retrive the data when it is updated (once a day)
gridoperator.register_callback_new_data(ec_forcast.set_smart_meter_data)

mp_contr.add_forcaster(ec_forcast, milp_ec, 'P_resid_ec')

##############
# BES
##############
milp_bes = BES_MILP_model(
    name='bes',
    E_min=0,
    E_max=20_000*3600, # J
    P_max_cha=20000, # W
    P_max_dis=20000, # W
    eta_cha=0.9, # 
    eta_dis=0.9 # 
    )

mp_contr.add_model(milp_bes)

##############
# DHWH 1
##############
milp_dhwh1 = DHW_MILP_model_Temp(name='dhwh1', P_nom=3600, C_tes=4200*100)
mp_contr.add_model(milp_dhwh1)

## Forcast for temperature in DHWH 1
dhwh1_forcast = Forcasting('generic_single_var_persistence','dot_m_demand', init_val=0)

mp_contr.add_forcaster(dhwh1_forcast, milp_dhwh1, 'dot_m_demand')


# ##############
# # DHWH 2
# ##############
# milp_dhwh2 = DHW_MILP_model_Temp(name='dhwh2', P_nom=3600, C_tes=4200*100)
# mp_contr.add_model(milp_dhwh2)

# ## Forcast for temperature in DHWH 1
# dhwh2_forcast = Forcasting('generic_single_var_persistence','dot_m_demand', init_val=0)

# mp_contr.add_forcaster(dhwh2_forcast, milp_dhwh2, 'dot_m_demand')



sim.add_model(mp_contr, watch_values=['E_BES_0_of_bes', 'P_el_of_bes','on_of_dhwh1']) # , watch_heavy=['P_resid_ec_of_EC'])
sim.connect_nothing(gridoperator, mp_contr)

sim.connect(battery_storage, mp_contr, ('E', 'E_BES_0_of_bes'), ('P_grid', 'P_flex_'))

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
