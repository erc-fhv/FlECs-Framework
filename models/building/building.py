import numpy as np
import pickle


class BuildingModel():
    '''
    Model of a building envelope for a simple building, reresented as a RC model which is black box identified from a SynPro Dataset
    '''
    def __init__(self, name, T_building_0=20) -> None:
        self.name = name

        # Parameters
        self.delta_t = 60  # s
        
        with open('models/building/fasade_model.pkl', mode='rb') as f:
            self.fasade_model = pickle.load(f)

        self._A = np.array([[0.99946908]])
        self._B = np.array([[1.27224559e-06, 1.29389956e-06]])
        self._F = np.array([[1.05513931e-06, 5.65074395e-04, 1.15661336e-06]])

        self._x = np.array([T_building_0])

        self.inputs = ['dot_Q_heat', 'dot_Q_cool', 'dot_Q_int', 'T_amb', 'I_dir', 'I_dif', 'I_s', 'I_w', 'I_n', 'I_e']
        self.outputs = ['T_building']

    def step(self, time, dot_Q_heat, dot_Q_cool, dot_Q_int, T_amb, I_dir, I_dif, I_s, I_w, I_n, I_e):
        dot_Q_sol = self.fasade_model.predict([[I_dir, I_dif, I_s, I_w, I_n, I_e]])[0]

        u = np.array([dot_Q_heat, dot_Q_cool])
        d = np.array([dot_Q_int, T_amb, dot_Q_sol])

        self._x = self._A@self._x.T + self._B@u.T + self._F@d.T

        return {'T_building':self._x[0]}
    
