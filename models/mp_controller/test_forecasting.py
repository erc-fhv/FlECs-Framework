from models.mp_controller.forcasting import Forcasting, GenericPersistenceForcasting
import numpy as np
import pandas as pd

def test_forecasting_type():
    fc = Forcasting(method='generic_single_var_persistence', inpt='val')

    assert isinstance(fc, GenericPersistenceForcasting)
   
def test_persistence_store_data():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)
    
    fc.set_data(1, **{'v1': 1.})
    fc.set_data(1, **{'v1': 2.})

    assert np.array_equal(fc.ser.values, np.array([np.nan, np.nan, 1., 2.]), equal_nan=True)
    
def test_persistence_forecasting():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)

    fc.set_data(1, v1= 1.)
    fc.set_data(1, v1= 2.)
    fc.set_data(1, v1= 3.)
    fc.set_data(1, v1= 4.)

    assert fc.get_forcast(1) == [1., 2., 3.]

def test_persistence_forecasting_longer():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)

    fc.set_data(1, v1=1.)
    fc.set_data(1, v1=2.)
    fc.set_data(1, v1=3.)
    fc.set_data(1, v1=4.)
    fc.set_data(1, v1=5.)

    assert fc.get_forcast(1) == [2., 3., 4.]

def test_persistence_forecasting_delay():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1', delay=3)
    fc.set_forcast_length(n=3)

    fc.set_data(1, v1=1.)
    fc.set_data(1, v1=2.)
    fc.set_data(1, v1=3.)
    fc.set_data(1, v1=4.)
    fc.set_data(1, v1=5.)
    fc.set_data(1, v1=6.)
    fc.set_data(1, v1=7.)

    assert fc.get_forcast(1) == [2., 3., 4.]


####################
# persistence_residual_load_smartmeter
####################
def test_persistence_smart_meter_set_sm_data():
    fc = Forcasting('persistence_residual_load_smartmeter')

    periods = 3
    data = np.random.random((periods, 2))*10

    index = pd.date_range(start="2020-01-01 00:00", periods=periods, freq="15min")
    df = pd.DataFrame(data, index=index, columns=['sm1', 'sm2'])

    fc.set_smart_meter_data(df)
    
    df_P_tot = df.sum(axis=1).rename('P_tot')
    
    assert all(fc.data['P_tot'].values == df_P_tot.values)
    # assert fc.last_valid_index == index[-1] # not applicable anymore, as the last valid index is now also determined by set_data, therefore in this scenario, there should be no valid data.

def test_persistence_smart_meter_set_data():
    fc = Forcasting('persistence_residual_load_smartmeter')

    periods = 3
    data = np.full((periods, 2), 10)
    index = pd.date_range(start="2020-01-01 00:00", periods=periods, freq="15min")

    for i, t in enumerate(index):
        fc.set_data(t, [i])

    df = pd.DataFrame(data, index=index, columns=['sm1', 'sm2'])
    fc.set_smart_meter_data(df)

    assert fc.data['P_resid'].to_list() == [20, 19, 18]


def test_persistence_smart_meter_get_fc_default():
    periods = 3

    fc = Forcasting('persistence_residual_load_smartmeter')
    fc.set_delta_t(15*60)
    fc.set_forcast_length(periods)

    data = np.full((periods, 2), 10)
    index = pd.date_range(start="2020-01-01 00:00", periods=periods, freq="15min")

    for i, t in enumerate(index):
        fc.set_data(t, [i])

    df = pd.DataFrame(data, index=index, columns=['sm1', 'sm2'])
    fc.set_smart_meter_data(df)

    forc = fc.get_forcast(pd.to_datetime('2020-01-01 00:00'))

    assert forc == [np.nan] * periods

def test_persistence_smart_meter_get_fc_valid_index():
    periods = 25*4 # 1 day 1h @ 15 min

    fc = Forcasting('persistence_residual_load_smartmeter')
    fc.set_delta_t(15*60)
    fc.set_forcast_length(3)

    for i, t in enumerate(pd.date_range(start="2020-01-01 00:00", end='2020-01-02 01:00:00', freq="15min")):
        fc.set_data(t, [i])

    p_sm = 24*4 # one day @ 15 min
    data = np.full((p_sm, 2), 10)
    df = pd.DataFrame(
        data, 
        index=pd.date_range(start="2020-01-01 00:00", periods=p_sm, freq="15min"),
        columns=['sm1', 'sm2'])
    
    fc.set_smart_meter_data(df)

    forc = fc.get_forcast(pd.Timestamp('2020-01-02 01:00:00'))

    assert forc == [20-5, 20-6, 20-7]

