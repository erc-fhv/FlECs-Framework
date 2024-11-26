import pandas as pd

class SynproElectricConsumption():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s
        
        self.df = pd.read_csv(r'data\synPro\synPRO_Dhw_H_3_1_App_9_Oc_18_MFHkl_MFH_5_Por_1_dhw_13258.dat', header=18, sep=';', index_col=2).drop(['YYYYMMDD', 'hhmmss'], axis=1)
        self.df.index = pd.to_datetime(self.df.index, unit='s').tz_localize('utc').tz_convert('Europe/Berlin')
        
        self.df = (self.df.loc[:, ['Q_dhw']]).rename({'Q_dhw': 'dot_Q_dhw'})

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()