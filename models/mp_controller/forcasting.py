import pandas as pd
import numpy as np
from typing import Protocol, Any, runtime_checkable


#################
# Protocol for the forecasting classes
#################
@runtime_checkable
class ForcastingProto(Protocol):
    def __init__(self) -> None:
        ...
    
    def set_forcast_length(self, n:int) -> None:
        ...
    
    def set_data(self, time, **inputs: Any):
        ...
    
    def get_forcast(self, time) -> list:
        ...


class Forcasting:
    """A factory class that creates a Forecasting object based on the provided method."""
    _registry = {}

    def __new__(cls, method, *args, **kwargs):
        """Create an instance of the appropriate registered class."""
        if method not in cls._registry:
            raise ValueError(f"No class registered for condition: {method}")
        forecasting_class = cls._registry[method]
        return forecasting_class(*args, **kwargs)

    @classmethod
    def register(cls, condition):
        """Register a class with the factory."""
        def decorator(klass):
            if not issubclass(klass, ForcastingProto):
                raise TypeError(f'The Forcasting class "{klass}" that was registered with Forcasting, does not implement the required protocol') 
            cls._registry[condition] = klass
            return klass
        return decorator


@Forcasting.register('generic_single_var_persistence')
class GenericPersistenceForcasting():
    def __init__(self, inpt:str, init_val=np.nan, delay=1):
        self.inputs = [inpt]
        self.inpt = inpt
        self.init_val = init_val
        self.delay = delay

    def get_forcast(self, time) -> list:
        return self.ser.loc[:self.periods-1].values.tolist()

    def set_data(self, time, **values) -> None:
        value = values[self.inpt]
        self.ser = self.ser.shift(-1)
        self.ser.loc[self.last_index] = value
    
    def set_forcast_length(self, n:int) -> None:
        self.periods = n
        self.ser = pd.Series(data=np.full(self.delay+self.periods, self.init_val), index=range(self.delay+self.periods))
        self.last_index = self.delay+self.periods-1


@Forcasting.register('persistence_residual_load')
class PersistenceResidualLoadForcasting():
    def __init__(self, init_val=np.nan, delay=1):
        self.inputs = ['P_tot', 'P_flex_']
        self.init_val = init_val
        self.delay = delay

    def get_forcast(self, time) -> list:
        return self.ser.loc[:self.periods-1].values.tolist()

    def set_data(self, time, P_tot, P_flex_) -> None:
        P_flex = sum(P_flex_)
        P_resid = P_tot - P_flex   # signs!!!?????????????????????????
        self.ser = self.ser.shift(-1)
        self.ser.loc[self.last_index] = P_resid
    
    def set_forcast_length(self, n:int) -> None:
        self.periods = n
        self.ser = pd.Series(data=np.full(self.delay+self.periods, self.init_val), index=range(self.delay+self.periods))
        self.last_index = self.delay+self.periods-1


@Forcasting.register('persistence_residual_load_smartmeter')
class PersistenceResidualSmartmeterLoadForcasting():
    def __init__(self, default_val=np.nan, delay_periods=1):
        self.inputs = ['P_flex_']

        self.default_val = default_val # returnd in case no forcast can be made (eg strart of simulation)
        self.delay_periods = delay_periods # delay between call and start of prediction horizon (usually one, as optimization start there)

        self.data = pd.DataFrame([], columns=['P_tot','P_flex', 'P_resid'])
        self.last_valid_index = pd.to_datetime('1990-01-01 00:00').tz_localize(tz='Europe/Berlin')
        self.last_valid_index = pd.to_datetime('1990-01-01 00:00').tz_localize(tz='Europe/Berlin')

    def get_forcast(self, time) -> list:
        # get last day if exists in data
        start_dt = time + self.timedelta_delay - pd.Timedelta(1, 'day') 
        end_dt = start_dt + self.timedelta_periods
        if end_dt <= self.last_valid_index and start_dt >= self.first_valid_index:
            return self.data.loc[start_dt:end_dt, 'P_resid'].to_list()

        # get last same weekday if exists in data
        start_dt = time + self.timedelta_delay - pd.Timedelta(7, 'day') 
        end_dt = start_dt + self.timedelta_periods
        if end_dt <= self.last_valid_index and start_dt >= self.first_valid_index:
            return self.data.loc[start_dt:end_dt, 'P_resid'].to_list()

        # Otherwise return default
        return [self.default_val] * self.periods

    def set_data(self, time, P_flex_) -> None:
        P_flex = sum(P_flex_)
        self.data.at[time, 'P_flex'] = P_flex

    def set_delta_t(self, delta_t:int) -> None:
        self.delta_t = delta_t
        self.timedelta_delay = pd.to_timedelta(self.delay_periods*delta_t, unit='s')
        if hasattr(self, 'periods'):
            self.timedelta_periods = pd.Timedelta((self.periods-1)*self.delta_t, unit='s')

    def set_forcast_length(self, n:int) -> None:  # TODO: add delta t to the atributes that are added by the controller!
        self.periods = n
        if hasattr(self, 'delta_t'):
            self.timedelta_periods = pd.Timedelta((n-1)*self.delta_t, unit='s')

    def set_smart_meter_data(self, df_P_daily):
        if not df_P_daily.empty:
            P_tot = df_P_daily.sum(axis=1).squeeze()
            self.data = self.data.reindex(self.data.index.union(P_tot.index)) # TODO: make nicer!
            self.data.loc[P_tot.index, 'P_tot'] = P_tot.values
            self.data['P_resid'] = self.data['P_tot'] - self.data['P_flex'] # signs!!!?????????????????????????
            self.last_valid_index = df_P_daily.index[-1]
            
            # get first valid index  # TODO: improve!
            df_usefull = self.data.dropna()
            if not df_usefull.empty:
                self.first_valid_index = df_usefull.index[0] 

