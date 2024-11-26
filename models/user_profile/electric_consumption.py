import pandas as pd

class SynproElectricConsumption():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s


        self.df = pd.read_csv(r'data\synPro\synPRO_el_sum_H_3_1_App_9_Oc_18_MFHkl_MFH_5_Por_1_el_26026.dat', header=10, sep=';', index_col=2).drop(['YYYYMMDD', 'hhmmss'], axis=1)
        self.df.index = pd.to_datetime(self.df.index, unit='s').tz_localize('utc').tz_convert('Europe/Berlin')
        
        self.df = (self.df.loc[:, ['P_el']])

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()