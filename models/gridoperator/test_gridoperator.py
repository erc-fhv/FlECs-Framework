import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from models.gridoperator.gridoperator import GridOperator


class SmartMeterMock():
    def __init__(self, name):
        self.name = name

    def retrieve_data(self):
        date_range = pd.date_range(start="2020-01-01 00:00", end="2020-01-02 00:00", freq="15min")
        random_values = np.random.randint(0, 2001, size=len(date_range))
        return pd.Series(data=random_values, index=date_range, name=self.name)

def test_gridoperator_initialization():
    gridoperator = GridOperator('name')
    assert gridoperator.name == 'name'
    assert gridoperator.inputs == []
    assert gridoperator.outputs == ['df_P_day']
    assert gridoperator.delta_t == 60*60*24

def test_gridoperator_register_smartmeter():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1')
    smartmeter1 = SmartMeterMock('sm2')
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    assert isinstance(gridoperator._smart_meter_models[0], SmartMeterMock)
    assert isinstance(gridoperator._smart_meter_models[1], SmartMeterMock)

# def test_gridoperator_step():
#     gridoperator = GridOperator('name')
#     smartmeter = SmartMeterMock('sm1')
#     smartmeter1 = SmartMeterMock('sm2')
#     gridoperator.register_smartmeter(smartmeter)
#     gridoperator.register_smartmeter(smartmeter1)

#     # print(gridoperator.step(1))