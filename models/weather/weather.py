import pandas as pd
from pathlib import Path


class SynproWeather():
    def __init__(self, name):
        self.name = name
        self.delta_t = 60  # s

        self.df = pd.read_csv(Path(r'data/synPro/synPRO_Htg_H_3_1_App_9_Oc_18_MFHkl_MFH_5_Por_1_htg_17033.dat'), header=45, sep=';', index_col=2).drop(['YYYYMMDD', 'hhmmss'], axis=1)
        self.df.index = pd.to_datetime(self.df.index, unit='s').shift(periods=+4, freq=pd.DateOffset(years = 1)).tz_localize('utc').tz_convert('Europe/Berlin') # shift to 2021, set timezone
        
        self.df = self.df.loc[:, ['t_amb', 'I_dir', 'I_dif', 'I_s', 'I_w', 'I_n', 'I_e']].rename({'t_amb': 'T_amb'}, axis=1)

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()
        