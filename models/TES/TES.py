import numpy as np
from scipy.linalg import expm

class TESModel():
    def __init__(self, name, delta_t=60, V=2, d=1200, N=3, U=0.338, T0=[293.15, 293.15, 293.15]) -> None:
        # Parameter
        self.delta_t   = delta_t
        self.c_p       = 4200 # J/(kg K)

        self.N         = N    # number of layers
        self.A_l       = (np.pi * (d/1000)**2)/4 # diameter of the tank in m 
        self.h         = (V*10**9)/((np.pi * d**2)/4) # height of the tank in mm
        self.x_l       = self.h / (self.N * 1000) # height of each layer in m
        self.m_l       = (V*1000)/self.N # mass of water in each layer in kg
        self.UA_m      = U * (np.pi * d * self.h / self.N)/10**6 # UA value of middle layers in W / K
        self.UA_a      = U * (np.pi * d * self.h / self.N + (d**2/4 * np.pi))/10**6 # UA value of outer layers in W / K
        self.UA        = [self.UA_a]+[self.UA_m]*(self.N-2)+[self.UA_a]
        self.C         = [self.m_l*self.c_p] * N # J / kg
        self.A         = np.zeros((self.N, self.N))
        self.B         = np.zeros((self.N, self.N+1))
        self.u         = np.zeros((1, self.N+1))
        self.dot_m     = np.zeros((self.N, self.N)) # dot_m[ein, aus]
        self.x         = np.array([T0])
        self.k         = [  0.6,   0.6,   0.6] # W/(m K)
        
        # inputs outputs 
        self.inputs  = ['dot_m_i_HP', 'dot_m_o_HP', 'dot_m_i_DHW', 'dot_m_o_DHW', 'T_i_HP', 'T_i_DHW', 'T_inf']
        self.outputs = ['T_0', 'T_1', 'T_2']
        self.name = name

    def step(self, dot_m_i_HP, dot_m_o_HP, dot_m_i_DHW, dot_m_o_DHW, T_i_HP, T_i_DHW, T_inf): #, time):
        dot_m_i = [ dot_m_i_HP] + [0]*(self.N-2) + [dot_m_i_DHW] # kg/s
        T_i     = [     T_i_HP] + [0]*(self.N-2) + [    T_i_DHW] # K
        dot_m_o = [dot_m_o_DHW] + [0]*(self.N-2) + [ dot_m_o_HP] # kg/s

        self.x = logic_heat_transfer(dot_m_i, dot_m_o, self.dot_m, self.UA, self.A, self.B, self.u, self.C, self.N, self.c_p, self.x, T_inf, T_i, self.delta_t, self.x_l, self.k, self.A_l)
        return {'T_0':self.x[0], 'T_1':self.x[1], 'T_2':self.x[2]}


def logic(dot_m_i, dot_m_o, dot_m, UA, A, B, u, C, N, c_p, x_prev, T_inf, T_i, delta_t, x_l, k, A_l):
    # check mass balance
    assert sum(dot_m_i) - sum(dot_m_o) == 0, 'mass balance not zero'

    #################
    # Mass balance
    #################
    # Zeroth Layer
    dot_m_net = dot_m_i[0] - dot_m_o[0]
    if dot_m_net > 0:
        dot_m[0, 1] = dot_m_net
        dot_m[1, 0] = 0
    else:
        dot_m[0, 1] = 0
        dot_m[1, 0] = -dot_m_net

    # Mid Layers
    for n in range(1, N-1):
        dot_m_net = dot_m_i[n] - dot_m_o[n] + dot_m[n-1, n] - dot_m[n, n-1]
        if dot_m_net > 0:
            dot_m[n, n+1] = dot_m_net
            dot_m[n+1, n] = 0
        else:
            dot_m[n, n+1] = 0
            dot_m[n+1, n] = -dot_m_net

    #################
    # A Matrix
    #################
    # Zeroth Layer (Top)
    A[0, 0]     = (-UA[0] - dot_m_o[0]*c_p - dot_m[0, 1]*c_p)/C[0]
    A[0, 1]     = (dot_m[1, 0]*c_p)/C[0]

    # N-2  Mid Layers
    for n in range(1, N-1):
        A[n, n-1] = (dot_m[n-1, n]*c_p)/C[n]
        A[n, n]   = (-UA[n] - dot_m_o[n]*c_p - dot_m[n, n+1]*c_p - dot_m[n, n-1]*c_p)/C[n]
        A[n, n+1] = (dot_m[n+1, n]*c_p)/C[n]

    # N-th Layer (Bottom)
    A[N-1, N-2] = (dot_m[N-2, N-1]*c_p)/C[N-1]
    A[N-1, N-1] = (-UA[N-1] - dot_m_o[N-1]*c_p - dot_m[N-1, N-2]*c_p)/C[N-1]

    #################
    # B-Vector
    #################
    for n in range(N):
        B[n,   0] = UA[n]/C[n]
        B[n, n+1] = c_p/C[n]

    #################
    # u-Vector
    #################
    u[0,0] = T_inf
    for n in range(N):
        u[0, n+1] = dot_m_i[n]*T_i[n]

    # discretize
    exponent = np.vstack((np.hstack((A, B)), np.zeros((B.shape[1], A.shape[1]+B.shape[1]))))*delta_t

    res = expm(exponent)

    Ad = res[:A.shape[0], :A.shape[1]]
    Bd = res[:B.shape[0], A.shape[1]:]

    x=Ad@x_prev.T+Bd@u.T
    
    return x

def logic_heat_transfer(dot_m_i, dot_m_o, dot_m, UA, A, B, u, C, N, c_p, x_prev, T_inf, T_i, delta_t, x_l, k, A_l):
    # logic with heat transfer between layers new

    # check mass balance
    assert sum(dot_m_i) - sum(dot_m_o) == 0, 'mass balance not zero'

    #################
    # Mass balance
    #################
    # Zeroth Layer
    dot_m_net = dot_m_i[0] - dot_m_o[0]
    if dot_m_net > 0:
        dot_m[0, 1] = dot_m_net
        dot_m[1, 0] = 0
    else:
        dot_m[0, 1] = 0
        dot_m[1, 0] = -dot_m_net

    # Mid Layers
    for n in range(1, N-1):
        dot_m_net = dot_m_i[n] - dot_m_o[n] + dot_m[n-1, n] - dot_m[n, n-1]
        if dot_m_net > 0:
            dot_m[n, n+1] = dot_m_net
            dot_m[n+1, n] = 0
        else:
            dot_m[n, n+1] = 0
            dot_m[n+1, n] = -dot_m_net

    #################
    # A Matrix
    #################
    # Zeroth Layer (Top)
    A[0, 0]     = (-UA[0] - dot_m_o[0]*c_p - dot_m[0, 1]*c_p)/C[0] - k[1]*A_l/(x_l*C[0])
    A[0, 1]     = (dot_m[1, 0]*c_p )/C[0]+ k[1]*A_l/(x_l*C[0])

    # N-2  Mid Layers
    for n in range(1, N-1):
        A[n, n-1] = (dot_m[n-1, n]*c_p)/C[n] + k[n]*A_l/(x_l*C[n])
        A[n, n]   = (-UA[n] - dot_m_o[n]*c_p - dot_m[n, n+1]*c_p - dot_m[n, n-1]*c_p)/C[n] - k[n]*A_l/(x_l*C[n]) - k[n+1]*A_l/(x_l*C[n])
        A[n, n+1] = (dot_m[n+1, n]*c_p)/C[n] + k[n+1]*A_l/(x_l*C[n])

    # N-th Layer (Bottom)
    A[N-1, N-2] = (dot_m[N-2, N-1]*c_p)/C[N-1] + k[N-1]*A_l/(x_l*C[N-1])
    A[N-1, N-1] = (-UA[N-1] - dot_m_o[N-1]*c_p - dot_m[N-1, N-2]*c_p)/C[N-1] - k[N-1]*A_l/(x_l*C[N-1])


    #################
    # B-Vector
    #################
    for n in range(N):
        B[n, 0] = UA[n]/C[n]
        B[n, n+1] = c_p/C[n]

    #################
    # u-Vector
    #################
    u[0,0] = T_inf
    for n in range(N):
        u[0, n+1] = dot_m_i[n]*T_i[n]

    # discretize

    exponent = np.vstack((np.hstack((A, B)), np.zeros((B.shape[1], A.shape[1]+B.shape[1]))))*delta_t

    res = expm(exponent)

    Ad = res[:A.shape[0], :A.shape[1]]
    Bd = res[:B.shape[0], A.shape[1]:]

    x=Ad@x_prev.T+Bd@u.T

    x   
    
    return x