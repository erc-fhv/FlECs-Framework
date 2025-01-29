import pandas as pd
from collections import deque

class SmartMeter():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s

        self.inputs = ['P_'] # P_ as list attribute (endswith '_')
        self.outputs = ['P_grid']

        self._P_quarter_hourly_data = pd.Series([], name=self.name)

    def step(self, time, P_):
        P_grid = sum(P_)
        # self._P_quarter_hourly_data[time] = P_grid

        return {'P_grid': P_grid}

    def retrieve_data(self):
        if self._P_quarter_hourly_data.empty:
            return pd.Series([], name=self.name)
        resampled_data = (self._P_quarter_hourly_data*self.delta_t).resample('15min').sum()
        del self._P_quarter_hourly_data
        self._P_quarter_hourly_data = pd.Series([], name=self.name)
        return resampled_data
        
