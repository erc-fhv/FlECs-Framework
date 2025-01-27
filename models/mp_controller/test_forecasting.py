from models.mp_controller.forcasting import Forcasting, GenericPersistenceForcasting
import numpy as np

def test_forecasting_type():
    fc = Forcasting(method='generic_single_var_persistence', inpt='val')

    assert isinstance(fc, GenericPersistenceForcasting)
   
def test_persistence_store_data():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)
    
    fc.set_data(**{'v1': 1.})
    fc.set_data(**{'v1': 2.})

    assert np.array_equal(fc.ser.values, np.array([np.nan, np.nan, 1., 2.]), equal_nan=True)
    
def test_persistence_forecasting():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)

    fc.set_data(v1= 1.)
    fc.set_data(v1= 2.)
    fc.set_data(v1= 3.)
    fc.set_data(v1= 4.)

    assert fc.get_forcast() == [1., 2., 3.]

def test_persistence_forecasting_longer():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1')
    fc.set_forcast_length(n=3)

    fc.set_data(v1=1.)
    fc.set_data(v1=2.)
    fc.set_data(v1=3.)
    fc.set_data(v1=4.)
    fc.set_data(v1=5.)

    assert fc.get_forcast() == [2., 3., 4.]

def test_persistence_forecasting_delay():
    fc = Forcasting(method='generic_single_var_persistence', inpt='v1', delay=3)
    fc.set_forcast_length(n=3)

    fc.set_data(v1=1.)
    fc.set_data(v1=2.)
    fc.set_data(v1=3.)
    fc.set_data(v1=4.)
    fc.set_data(v1=5.)
    fc.set_data(v1=6.)
    fc.set_data(v1=7.)

    assert fc.get_forcast() == [2., 3., 4.]

