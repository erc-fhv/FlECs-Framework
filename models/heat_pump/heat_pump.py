import numpy as np
import pandas as pd

class HeatPumpEventBased():
    def __init__(self, name, delta_t=60, eta=0.5, P_el_nom=2000) -> None:
        # Parameter
        self.delta_t = delta_t

        self.eta      = eta
        self.P_el_nom = P_el_nom # nominal Power

        # internal Parameter
        self._cop_fun = lambda Tsource, Tsink, eta: (Tsink+273.15)/((Tsink+273.15) - (Tsource+273.15)) * eta
        
        # inputs outputs 
        self.inputs  = ['state', 'T_source', 'T_sink']
        self.outputs = ['cop', 'P_el', 'dot_Q_hp']
        self.name = name

    def step(self, time, state, T_source, T_sink):
        if state == 'on':
            P_el = self.P_el_nom
            next_exec_time = pd.Timedelta(60, 'sec') + time
        else:
            P_el = 0
            next_exec_time = pd.Timedelta(1, 'day') + time
        cop = self._cop_fun(T_source, T_sink, self.eta)
        dot_Q_hp = P_el * cop

        
        return {'next_exec_time': next_exec_time, 'cop':cop, 'P_el':P_el, 'dot_Q_hp':dot_Q_hp}
    

class HeatPumpWControlEventBased():
    def __init__(self, name, delta_t=60, eta=0.5, dot_Q_hp_nom=10000, P_el_max=2000, P_el_min=1000) -> None:
        # Parameter
        self.delta_t = delta_t

        self.eta      = eta  # "Gütegrad"
        self.dot_Q_hp_nom = dot_Q_hp_nom # nominal Power
        self.P_el_max = P_el_max
        self.P_el_min = P_el_min

        # internal Parameter
        self._cop_fun = lambda Tsource, Tsink, eta: (Tsink+273.15)/((Tsink+273.15) - (Tsource+273.15)) * eta
        
        # inputs outputs 
        self.inputs  = ['state', 'T_source', 'T_sink']
        self.outputs = ['P_el', 'dot_Q_hp']
        self.name = name

    def step(self, time, state, T_source, T_sink):
        if state == 'on':
            dot_Q_hp_nom = self.dot_Q_hp_nom
            cop = self._cop_fun(T_source, T_sink, self.eta) # calc COP
            P_el_setpoint = dot_Q_hp_nom / cop # Calculate nominal P_el at current COP
            P_el = max(self.P_el_min, min(P_el_setpoint, self.P_el_max)) # Clip electrical power
            dot_Q_hp = P_el * cop
            
            next_exec_time = pd.Timedelta(60, 'sec') + time
        else:
            dot_Q_hp = 0
            P_el = 0
            next_exec_time = pd.Timedelta(1, 'day') + time

        return {'next_exec_time': next_exec_time, 'P_el':P_el, 'dot_Q_hp':dot_Q_hp}
        
