import numpy as np
from models.TES.TES_logic import logic_heat_transfer

class TESModel():
    def __init__(self, name, delta_t=60, V=0.1, d=400, N=10, U=0.766, k_1=8.2, P_el_nom=2000, h_he=300, T0=[40., 40., 40., 40., 40., 40., 40., 40., 40., 40.]) -> None:
        ''''
        Thermal energy storage model with input from electric heating element and domestic hot water usage

        Parameter
        ---------
        name : str, name of the model
        delta_t : int, timestep in s, default 60s
        V : float, volume of TES in m^3
        d : float, inner diameter in mm
        N : int, number of layers (no unit)
        U : float, U-value in W//(m^2 K), default 0.766 W/(m^2 K), source: https://doi.org/10.1016/j.enbuild.2010.04.013 
        k_1 : float, effective thermal conductivity in W/(m K), default 8.2 W/(m K), source: https://doi.org/10.1016/j.enbuild.2010.04.013 
        P_el_nom : int, nominal power in W
        h_he : height of the heating element in mm
        T0 : list of floats, temperature in layers at time t0 in K

        Inputs
        ---------
        dot_m_i_DHW : float, fresh water mass flow input from domestic hot water usage in kg/s
        dot_m_o_DHW : float, mass flow output from domestic hot water usage in kg/s
        T_i_DHW : float, temperature of mass flow input from domestic hot water usage in K
        state : binary, variable controlling the heating element (no unit)
        T_inf : float, temperature of surrounding in K

        Outputs
        ---------
        T_tw : float, temperature in layer of thermal well in °C (same layer as heating element ends)
        T_0 : float, temperature in top layer in °C
        '''

        self.inputs  = ['dot_m_o_DHW', 'T_i_DHW', 'state', 'T_inf']
        self.outputs = ['T_tw', 'T_0']
        self.name    = name

        # Parameters
        self.delta_t   = delta_t # s
        self.P_el_nom  = P_el_nom # W
        self.c_p       = 4200 # J/(kg K)
        self.N         = N # number of layers
        self.A_l       = (np.pi * (d/1000)**2)/4 # inside area of the tank in m 
        self.h         = (V*10**9)/((np.pi * d**2)/4) # height of the tank in mm
        self.x_l       = self.h / (self.N * 1000) # height of each layer in m
        self.m_l       = (V*1000)/self.N # mass of water in each layer in kg
        self.UA_m      = U * (np.pi * d * self.h / self.N)/10**6 # UA value of middle layers in W / K
        self.UA_a      = U * (np.pi * d * self.h / self.N + (d**2/4 * np.pi))/10**6 # UA value of outer layers in W / K
        self.UA        = [self.UA_a]+[self.UA_m]*(self.N-2)+[self.UA_a] # list of UA values for each layer
        self.C         = [self.m_l*self.c_p] * N # J / kg
        self.A         = np.zeros((self.N, self.N)) # A matrix
        self.B         = np.zeros((self.N, self.N+2)) # B matrix
        self.u         = np.zeros(self.N+2) # u vector
        self.dot_m     = np.zeros((self.N, self.N)) # dot_m[ein, aus]
        self.x         = np.array(T0) + 273.15 # vector containing starting temperatures in K
        self.k         = [  0] *self.N # starting k values (values will be determined in logic) W/(m K)
        self.k_1       = k_1 # W/(m K)
        self.k_2       = 999999 # W/(m K)
        self.he_layers = int(np.ceil(h_he/(self.h/self.N))) # layers of the tank receiving heat from heating element directly
        self.P_el      = [0] * (self.N-self.he_layers) + [self.P_el_nom/self.he_layers] * self.he_layers # list of electrical power input of each layer in W
        

    def step(self, time, dot_m_o_DHW, T_i_DHW, T_inf, state):
        dot_m_i = [             0] + [0]*(self.N-2) + [   dot_m_o_DHW] # kg/s
        T_i     = [             0] + [0]*(self.N-2) + [T_i_DHW+273.15] # K
        dot_m_o = [   dot_m_o_DHW] + [0]*(self.N-2) + [             0] # kg/s

        self.x = logic_heat_transfer(dot_m_i, dot_m_o, self.dot_m, self.UA, self.A, self.B, self.u, self.C, self.N, self.c_p, self.x, T_inf+273.15, T_i, self.delta_t, self.x_l, self.k, self.A_l, self.k_1, self.k_2, self.P_el, state)
        return {'T_tw':(self.x[6]-273.15), 'T_0':(self.x[0]-273.15)}
