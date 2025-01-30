import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from models.gridoperator.gridoperator import GridOperator


class SmartMeterMock():
    def __init__(self, name, mul, start_dt="2020-01-01 00:00"):
        self.name = name
        date_range = pd.date_range(start=start_dt, end="2020-01-02 00:00", freq="15min")
        values = np.arange(len(date_range))*mul
        self.values = pd.Series(data=values, index=date_range, name=self.name)

    def retrieve_data(self):
        return self.values
    
class ECMock():
    def __init__(self):
        self.name = 'ec'
        self.df_P_day = pd.DataFrame([])
   
    def set_data(self, df_P_day):
        self.df_P_day = df_P_day
        

def test_gridoperator_initialization():
    gridoperator = GridOperator('name')
    assert gridoperator.name == 'name'
    assert gridoperator.inputs == []
    assert gridoperator.outputs == ['df_P_day']
    assert gridoperator.delta_t == 60*60*24

def test_gridoperator_register_smartmeter():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1', 10)
    smartmeter1 = SmartMeterMock('sm2', 10)
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    assert isinstance(gridoperator._smart_meter_models[0], SmartMeterMock)
    assert isinstance(gridoperator._smart_meter_models[1], SmartMeterMock)

def test_gridoperator_step_w_smartmeter():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1', 10)
    smartmeter1 = SmartMeterMock('sm2', 20)
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    outputs = gridoperator.step(1)
    assert outputs['df_P_day'].iloc[0, 0] == 0
    assert outputs['df_P_day'].iloc[1, 0] == 10
    assert outputs['df_P_day'].iloc[1, 1] == 20
    assert outputs['df_P_day'].index[0] == pd.to_datetime("2020-01-01 00:00")

def test_gridoperator_step_w_ec():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1', 10)
    smartmeter1 = SmartMeterMock('sm2', 20)
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    ec = ECMock()
    gridoperator.register_callback_new_data(ec.set_data)

    outputs = gridoperator.step(1)

    assert outputs['df_P_day'].equals(ec.df_P_day)

def test_gridoperator_multi_step():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1', 10)
    smartmeter1 = SmartMeterMock('sm2', 20)
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    ec = ECMock()
    gridoperator.register_callback_new_data(ec.set_data)

    outputs = gridoperator.step(1)
    outputs = gridoperator.step(2)
    outputs = gridoperator.step(2)

    assert outputs['df_P_day'].equals(ec.df_P_day)

def test_gridoperator_faulty_data():
    gridoperator = GridOperator('name')
    smartmeter = SmartMeterMock('sm1', 10, start_dt="2020-01-01 12:00")
    smartmeter1 = SmartMeterMock('sm2', 20)
    gridoperator.register_smartmeter(smartmeter)
    gridoperator.register_smartmeter(smartmeter1)

    outputs = gridoperator.step(1)
    assert np.isnan(outputs['df_P_day'].iloc[0, 0]) 
    assert np.isnan(outputs['df_P_day'].loc["2020-01-01 11:45", 'sm1']) 