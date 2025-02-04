import pandas as pd
from collections import deque

class SmartMeter():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s

        self.inputs = ['P_'] # P_ as list attribute (endswith '_')
        self.outputs = ['P_grid']

        self.reccords = []

    def step(self, time, P_):
        P_grid = sum(P_)
        self.reccords.append((time, P_grid))
        return {'P_grid': P_grid}

    def retrieve_data(self) -> pd.Series:
        '''retrieve the quarter hourly Energy as pd.Series
        data only contains new values since the last retrieval'''

        if not self.reccords:
            return pd.Series([], name=self.name)
        
        df = pd.DataFrame.from_records(
            self.reccords, 
            columns=['index', self.name], 
            index='index'
            )
        self.reccords = []
   
        if df.shape[0] < 15:
            return pd.Series([], name=self.name)
        
        ser = df.squeeze()
        # resampled_data = (ser*self.delta_t).resample('15min').sum()
        resampled_data = ser.resample('15min').mean()
        
        return resampled_data
        
