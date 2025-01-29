import numpy as np
from scipy.linalg import expm


def logic_heat_transfer(dot_m_i, dot_m_o, dot_m, UA, A, B, u, C, N, c_p, x_prev, T_inf, T_i, delta_t, x_l, k, A_l, k_1, k_2, P_el, state):
    # logic with heat transfer between layers

    #################
    # Effective thermal conductivity
    #################
  
    for n in range(1, N):
        if x_prev[0][n-1] >= x_prev[0][n]:
            k[n] = k_1
        elif x_prev[0][n-1] < x_prev[0][n]:
            k[n] = k_2

    # check mass balance
    assert sum(dot_m_i) - sum(dot_m_o) == 0, 'mass balance not zero'

    #################
    # Mass balance
    #################
    # Zeroth Layer (Top)
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
        B[n, N+1] = P_el[n]/C[n]
    
    #################
    # u-Vector
    #################
    u[0,0] = T_inf
    u[0, N+1] = state
    for n in range(N):
        u[0, n+1] = dot_m_i[n]*T_i[n]

    # discretize

    # discretize
    exponent = np.vstack((np.hstack((A, B)), np.zeros((B.shape[1], A.shape[1]+B.shape[1]))))*delta_t

    res = expm(exponent)

    Ad = res[:A.shape[0], :A.shape[1]]
    Bd = res[:B.shape[0], A.shape[1]:]

    x=Ad@x_prev.T+Bd@u.T
    
    return x