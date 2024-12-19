import pandas as pd

class GridOperator():
    def __init__(self, name, delta_t=60*60*24, smart_meter_models=[]):
        self.name = name
        self.delta_t = delta_t
        self.inputs = []
        self.outputs = ['df_P_day']
        self._smart_meter_models = smart_meter_models

    def register_smartmeter(self, smart_meter_model):
        self._smart_meter_models += [smart_meter_model]

    def step(self, time):
        pd.Series([]).rename()
        df_P_day = pd.concat(
            objs=[sm.retrieve_data() for sm in self._smart_meter_models], 
            axis=1
            )
        return {'df_P_day': df_P_day}