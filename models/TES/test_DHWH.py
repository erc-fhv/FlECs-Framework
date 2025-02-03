import pytest
import numpy as np
from DHWH import TESModel
from unittest.mock import MagicMock, patch

@pytest.fixture
def mocked_TES_model():
    """
    Provides a mocked instance of DHWHModel for testing.
    """
    model = TESModel(
        name="TestDHWH",
        delta_t=60, 
        V=0.1, 
        d=400, 
        N=10, 
        U=0.766, 
        k_1=8.2, 
        P_el_nom=2000, 
        h_he=300, 
        T0=[40., 40., 40., 40., 40., 40., 40., 40., 40., 40.]
                     )
    yield model

def test_initialization(mocked_TES_model):
    """
    Test the initialization of the DHWHModel.
    """
    model = mocked_TES_model
    assert model.name == "TestDHWH"
    assert model.x[0][3] ==  313.15 # Default thermal well temperature
    assert isinstance(model.inputs, list)
    assert isinstance(model.outputs, list)

def test_step_method_with_demand(mocked_TES_model):
    """
    Test the `step` method of DHWHModel with valid inputs.
    """
    model = mocked_TES_model
    result = model.step(
        time=0,
        dot_m_o_DHW=0.1,
        T_i_DHW=283.15,
        T_inf=283.15,
        state=0
    )
    assert "T_tw" in result
    assert np.isclose(result["T_tw"], 313.03895963 - 273.15)

def test_step_method_heating_without_demand(mocked_TES_model):
    """
    Test the `step` method of DHWHModel with valid inputs.
    """
    model = mocked_TES_model
    result = model.step(
        time=0,
        dot_m_o_DHW=0,
        T_i_DHW=283.15,
        T_inf=283.15,
        state=1
    )
    assert "T_tw" in result
    assert np.isclose(result["T_tw"], 313.85447819 - 273.15)

def test_step_method_without_demand_heating(mocked_TES_model):
    """
    Test the `step` method of DHWHModel with valid inputs.
    """
    model = mocked_TES_model
    result = model.step(
        time=0,
        dot_m_o_DHW=0,
        T_i_DHW=283.15,
        T_inf=283.15,
        state=0
    )
    assert "T_tw" in result
    assert np.isclose(result["T_tw"], 313.14671732 - 273.15)
