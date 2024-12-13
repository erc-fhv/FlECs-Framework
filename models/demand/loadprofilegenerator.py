import pandas as pd
from pathlib import Path

class Household():
    def __init__(self, name, lpg_dir):
        '''
        Specifies a household/user from a LoadProfileGenerator results directory
        '''
        self.name = name
        self.dir = Path(lpg_dir)
        self.delta_t = 60*15  # s
        
        P_el = pd.read_csv(self.dir.joinpath(Path('SumProfiles_900s.Electricity.csv')), sep=';', header=0, index_col=1).drop(['Electricity.Timestep'], axis=1)
        P_el.index = pd.to_datetime(P_el.index, format="%d.%m.%Y %H:%M").tz_localize(tz='Etc/GMT-1').tz_convert('Europe/Berlin')
        P_el = P_el.rename({'Sum [kWh]': 'P_el'}, axis=1)/0.25*1000

        dot_m_ww = pd.read_csv(self.dir.joinpath(Path('SumProfiles_900s.Warm Water.csv')), sep=';', header=0, index_col=1).drop(['Warm Water.Timestep'], axis=1)
        dot_m_ww.index = pd.to_datetime(dot_m_ww.index, format="%d.%m.%Y %H:%M").tz_localize(tz='Etc/GMT-1').tz_convert('Europe/Berlin')
        dot_m_ww = dot_m_ww.rename({'Sum [L]': 'dot_m_ww'}, axis=1)/900  # l/15min ~> kg/s

        dot_Q_gain_int = pd.read_csv(self.dir.joinpath(Path('SumProfiles_900s.Inner Device Heat Gains.csv')), sep=';', header=0, index_col=1).drop(['Inner Device Heat Gains.Timestep'], axis=1)
        dot_Q_gain_int.index = pd.to_datetime(dot_Q_gain_int.index, format="%d.%m.%Y %H:%M").tz_localize(tz='Etc/GMT-1').tz_convert('Europe/Berlin')
        dot_Q_gain_int = dot_Q_gain_int.rename({'Sum [kWh]': 'dot_Q_gain_int'}, axis=1)/0.25*1000  # kWh/15min ~> W

        
        self.df = pd.concat([P_el, dot_m_ww, dot_Q_gain_int], axis=1)

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()