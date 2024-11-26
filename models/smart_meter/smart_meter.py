import pandas as pd

class SmartMeter():
    def __init__(self, name, n_loads=1):
        self.name = name
        self.delta_t = 60  # s

        self.inputs = [f'P_{n}' for n in range(n_loads)]
        self.outputs = ['P_Grid', 'P_quarterhourly_data']

        self._P_quarter_hourly_data = pd.DataFrame([])

    def step(self, time, *P_behind_meter):
        P_grid = sum(P_behind_meter)
        self._P_quarter_hourly_data[time, 'P'] = P_grid

        return {'P_Grid': P_grid}

    def retrieve_data(self):
        return self._P_quarter_hourly_data # seach for / implement 'pop method' which empties dataframe but returns the values
        

class GridOperator():
    def __init__(self, *smart_meter_models):
        self.smart_meter_models = smart_meter_models

    def step(self, time, inputs):
        for smart_meter_model in self.smart_meter_models:
            self.smart_meter_data = smart_meter_model.retrieve_data()
