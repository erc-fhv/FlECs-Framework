import pandas as pd
from pathlib import Path
from pvlib.iotools import get_pvgis_hourly

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


class PvgisPV():
    def __init__(self, name, 
            latitude  = 47.440878,        # In decimal degrees, between -90 and 90, north is positive (ISO 19115)
            longitude = 9.996436,         # In decimal degrees, between -180 and 180, east is positive (ISO 19115)
            start = '2009',               # SEVA: time index has to start one year before the relevant year due to time zone conversion
            end   = '2010',               # SEVA: time index goes until '2007-01-01 00:00:00+01:00'
            surface_tilt = 0,             # Tilt angle from horizontal plane
            surface_azimuth = 180,        # Orientation (azimuth angle) of the (fixed) plane. Clockwise from north (north=0, east=90, south=180, west=270)
            usehorizon = True,            # Include effects of horizon
            pvcalculation = True,         # Return estimate of hourly PV production
            peakpower = 5,                # Nominal power of PV system in kW
            pvtechchoice = 'crystSi',     # ({'crystSi', 'CIS', 'CdTe', 'Unknown'}, default: 'crystSi')
            mountingplace = 'building',   # ({'free', 'building'}, default: free) – Type of mounting for PV system. Options of ‘free’ for free-standing and ‘building’ for building-integrated.
            loss = 15,                    # (float, default: 0) – Sum of PV system losses in percent. Required if pvcalculation=True
            optimal_surface_tilt = True,  # (bool, default: False) – Calculate the optimum tilt angle. Ignored for two-axis tracking
            optimalangles = True,         # (bool, default: False) – Calculate the optimum tilt and azimuth angles. Ignored for two-axis tracking.
            ):
        '''
        PV model based on the pvgis model via pvlib with hourly resolution.

        Parameter:
        ---------

        latitude : In decimal degrees, between -90 and 90, north is positive (ISO 19115)
        longitude : In decimal degrees, between -180 and 180, east is positive (ISO 19115)
        start : start time, time index has to start one year before the relevant year due to time zone conversion
        end : end time time index goes until
        surface_tilt : Tilt angle from horizontal plane
        surface_azimuth : Orientation (azimuth angle) of the (fixed) plane. Clockwise from north (north=0, east=90, south=180, west=270)
        usehorizon : Include effects of horizon
        pvcalculation : Return estimate of hourly PV production
        peakpower : Nominal power of PV system in kW
        pvtechchoice : ({'crystSi', 'CIS', 'CdTe', 'Unknown'}, default: 'crystSi')
        mountingplace : ({'free', 'building'}, default: free) – Type of mounting for PV system. Options of ‘free’ for free-standing and ‘building’ for building-integrated.
        loss : (float, default: 0) – Sum of PV system losses in percent. Required if pvcalculation=True
        optimal_surface_tilt : (bool, default: False) – Calculate the optimum tilt angle. Ignored for two-axis tracking
        optimalangles : (bool, default: False) – Calculate the optimum tilt and azimuth angles. Ignored for two-axis tracking.

        Inputs:
        ------
        None

        Outputs:
        -------
        P_pv : float, electrical PV system power in W (feedin < 0)

        '''
        self.name = name
        self.delta_t = 3600 # s

        data, inputs, metadata = get_pvgis_hourly(
            latitude             = latitude, 
            longitude            = longitude,
            start                = start, 
            end                  = end, 
            surface_tilt         = surface_tilt, 
            surface_azimuth      = surface_azimuth, 
            usehorizon           = usehorizon, 
            pvcalculation        = pvcalculation, 
            peakpower            = peakpower, 
            pvtechchoice         = pvtechchoice, 
            mountingplace        = mountingplace, 
            loss                 = loss, 
            optimal_surface_tilt = optimal_surface_tilt, 
            optimalangles        = optimalangles           
        )

        # reindexing with timezone aware index rounded to full hours
        data.index = data.index.round('h').tz_convert('Europe/Vienna')
        self.df = -data[['P']].rename({'P': 'P_pv'}, axis='columns')

        self.inputs = []
        self.outputs = list(self.df.columns)

    def step(self, time):
        return self.df.loc[time].to_dict()




