import pandas as pd

class GridOperator():
    def __init__(self, *smart_meter_models):
        self.smart_meter_models = smart_meter_models

    def step(self, time, inputs):
        for smart_meter_model in self.smart_meter_models:
            self.smart_meter_data = smart_meter_model.retrieve_data()