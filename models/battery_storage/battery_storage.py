
class BatteryStorage:
    def __init__(self, 
                 delta_t             =         3600, # s
                 E_0                 =  2500 * 3600, # J
                 E_max               = 50000 * 3600, # J
                 E_min               =            0, # J
                 eta_charge          =         0.95, #
                 eta_discharge       =         0.95, #
                 P_max_charge        =        10000, # W
                 P_max_discharge     =        10000, # W
                 self_discharge_rate =        2.e-8 # 1/s
                 ) -> None:
        '''
        Storage model with charging, discharging efficiencys and selfdischarge

        Parameters
        ----------
        delta_t : int, timestep in s, default 60s, 
        E_max : float, Maximum capacity in J
        E_min : float, Minimum capacity in J
        eta_charge : float, charging efficiency (no unit)
        eta_discharge : float, discharging efficiency (no unit)
        P_max_charge : float, maximum charging Power in W
        P_max_discharge : float, maximum discharging Power in W
        self_discharge_rate : float selfdischarge rate in 1/s
        '''

        self.inputs  = ['P_set']
        self.outputs = ['P_grid', 'E']

        # Parameters
        self.delta_t             = delta_t
        self.E_max               = E_max
        self.E_min               = E_min
        self.eta_charge          = eta_charge
        self.eta_discharge       = eta_discharge   
        self.P_max_charge        = P_max_charge  
        self.P_max_discharge     = P_max_discharge
        self.self_discharge_rate = self_discharge_rate

        # State
        self.E         = E_0  # J

    def step(self, time, P_set):
        '''
        P_set : Setpoint Power: P_set>0... discharging, P_set<0... charging
        '''

        P_set_valid = min(self.P_max_discharge, max(P_set, -self.P_max_charge))  # maximum / minimum power constraint

        # calculate potential new capacity
        if P_set_valid < 0: 
            E_new = self.E - P_set_valid * self.delta_t * self.eta_charge
        else:
            E_new = self.E - P_set_valid * self.delta_t / self.eta_discharge

        # check limits and adjust
        if E_new < self.E_min: # storage empty
            P_grid = (self.E - self.E_min) / self.delta_t * self.eta_discharge
            self.E = self.E_min
        elif E_new > self.E_max: # storage full
            P_grid = (self.E - self.E_max) / self.delta_t / self.eta_charge
            self.E = self.E_max
        else:
            P_grid = P_set_valid
            self.E = E_new

        # apply self discharge
        self.E = self.E*(1-self.self_discharge_rate*self.delta_t)

        return {'P_grid': P_grid, 'E': self.E}

