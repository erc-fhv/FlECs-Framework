class Grid():
    def __init__(self, name):
        '''
        A Simple Grid model
        
        Parameters
        ----------
        name : Name of the model
        
        Inputs:
        -------
        P_ : Loads and generation powers, consumption > 0

        Outputs:
        --------
        P_substation : residual load at the substation
        '''
        self.name = name
        self.delta_t = 60  # s

        self.inputs = [f'P_'] 
        self.outputs = ['P_substation']

    def step(self, time, P_):
        P_substation = sum(P_)
        return {'P_substation': P_substation}
    