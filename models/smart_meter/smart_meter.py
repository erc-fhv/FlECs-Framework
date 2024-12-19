import pandas as pd

class SmartMeter():
    def __init__(self, name, n_loads=1):
        self.name = name
        self.delta_t = 60  # s

        self.inputs = [f'P_{n}' for n in range(n_loads)]
        self.outputs = ['P_grid']

        self._P_quarter_hourly_data = pd.Series([], name=self.name)

    def step(self, time, **P_behind_meter):
        P_grid = sum(P_behind_meter.values())
        self._P_quarter_hourly_data[time] = P_grid

        return {'P_grid': P_grid}

    def retrieve_data(self):
        if self._P_quarter_hourly_data.empty:
            return pd.Series([], name=self.name)
        resampled_data = (self._P_quarter_hourly_data*self.delta_t).resample('15min').sum()
        del self._P_quarter_hourly_data
        self._P_quarter_hourly_data = pd.Series([], name=self.name)
        return resampled_data
        
