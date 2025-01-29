import pandas as pd
from pathlib import Path

class SynproPV():
    def __init__(self, name, P_pv_peak=50000):
        self.name = name
        self.delta_t = 60  # s

        self.df = pd.read_csv(Path(r'data/synPro/synPRO_Htg_H_3_1_App_9_Oc_18_MFHkl_MFH_5_Por_1_htg_17033.dat'), header=45, sep=';', index_col=2).drop(['YYYYMMDD', 'hhmmss'], axis=1)
        self.df.index = pd.to_datetime(self.df.index, unit='s').shift(periods=+4, freq=pd.DateOffset(years = 1)).tz_localize('utc').tz_convert('Europe/Berlin') # shift to 2021, set timezone
        
        self.df = (self.df.loc[:, ['P_pvn']]*(-P_pv_peak)).rename({'P_pvn': 'P_pv'}, axis=1)

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()