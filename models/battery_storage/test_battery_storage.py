from models.battery_storage.battery_storage import BatteryStorage
import numpy as np

def test_initialization():
    batterystorage = BatteryStorage(name='battery_storage_model1')
    assert batterystorage.name                == 'battery_storage_model1'
    assert batterystorage.delta_t             ==         3600 # s
    assert batterystorage.E                   ==  2500 * 3600 # J
    assert batterystorage.E_max               == 50000 * 3600 # J
    assert batterystorage.E_min               ==            0 # J
    assert batterystorage.eta_charge          ==         0.95 #
    assert batterystorage.eta_discharge       ==         0.95 #
    assert batterystorage.P_max_charge        ==        10000 # W
    assert batterystorage.P_max_discharge     ==        10000 # W
    assert batterystorage.self_discharge_rate ==        2.e-8 # 1/s

def test_step_normal_charge():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      2 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =             1, #
                 eta_discharge       =             1, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, 2.)
    assert np.isclose(output['P_grid'], 2.)
    assert np.isclose(output['E'],      4.*3600)

def test_step_normal_discharge():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      3 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =             1, #
                 eta_discharge       =             1, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, -2.)
    assert np.isclose(output['P_grid'], -2.)
    assert np.isclose(output['E'],      1.*3600)

def test_step_over_charge():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      4 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =             1, #
                 eta_discharge       =             1, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, 2.)
    assert np.isclose(output['P_grid'], 1.)
    assert np.isclose(output['E'],      5.*3600)

def test_step_over_discharge():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      1 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =             1, #
                 eta_discharge       =             1, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, -2.)
    assert np.isclose(output['P_grid'], -1.)
    assert np.isclose(output['E'],      0.*3600)

def test_step_charging_effiency():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      1 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =           0.8, #
                 eta_discharge       =             1, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, 2.)
    assert np.isclose(output['P_grid'], 2)
    assert np.isclose(output['E'], (1+2*0.8)*3600)

def test_step_discharging_effiency():
    batterystorage = BatteryStorage(
                 name                = 'battery_storage_1',
                 delta_t             =          3600, # s
                 E_0                 =      3 * 3600, # J
                 E_max               =      5 * 3600, # J
                 E_min               =             0, # J
                 eta_charge          =             1, #
                 eta_discharge       =           0.8, #
                 P_max_charge        =             2, # W
                 P_max_discharge     =             2, # W
                 self_discharge_rate =             0 # 1/s
    )
    output = batterystorage.step(1, -2.)
    assert np.isclose(output['P_grid'], -2)
    assert np.isclose(output['E'], (3-2/0.8)*3600)
    
