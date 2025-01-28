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
    
    def set_data(self, **inputs: Any):
        ...
    
    def get_forcast(self) -> list:
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

    def get_forcast(self) -> list:
        return self.ser.loc[:self.periods-1].values.tolist()

    def set_data(self, **values) -> None:
        value = values[self.inpt]
        self.ser = self.ser.shift(-1)
        self.ser.loc[self.last_index] = value
    
    def set_forcast_length(self, n:int) -> None:
        self.periods = n
        self.ser = pd.Series(data=np.full(self.delay+self.periods, self.init_val), index=range(self.delay+self.periods))
        self.last_index = self.delay+self.periods-1


@Forcasting.register('persistence_residual_load')
class GenericPersistenceForcasting():
    def __init__(self, init_val=np.nan, delay=1):
        self.inputs = ['P_tot', 'P_flex_']
        self.init_val = init_val
        self.delay = delay

    def get_forcast(self) -> list:
        return self.ser.loc[:self.periods-1].values.tolist()

    def set_data(self, P_tot, P_flex_) -> None:
        P_flex = sum(P_flex_)
        P_resid = P_tot - P_flex   # signs!!!?????????????????????????
        self.ser = self.ser.shift(-1)
        self.ser.loc[self.last_index] = P_resid
    
    def set_forcast_length(self, n:int) -> None:
        self.periods = n
        self.ser = pd.Series(data=np.full(self.delay+self.periods, self.init_val), index=range(self.delay+self.periods))
        self.last_index = self.delay+self.periods-1

