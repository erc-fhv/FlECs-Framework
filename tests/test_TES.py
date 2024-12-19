import unittest
import numpy as np
import sys
sys.path.append('./GEA-Szenario/') 
from models.TES.TES import TESModel

class TestTES(unittest.TestCase):

    def setUp(self):
        # set up of a TES model for testing
        self.TES = TESModel('test')

    def test_initial_conditions(self, name='test'):
        # test initialization of the model
        self.assertEqual(self.TES.delta_t,                          60) # s
        self.assertEqual(self.TES.N,                                 3) # 
        self.assertAlmostEqual(self.TES.h,           1768.39, places=2) # mm
        self.assertAlmostEqual(self.TES.m_l,          666.67, places=2) # kg
        self.assertAlmostEqual(self.TES.UA_m,     0.75111111, places=6) # W / K
        self.assertAlmostEqual(self.TES.UA_a,     1.13338011, places=6) # W / K
        self.assertEqual(self.TES.C, [2800000.0, 2800000.0, 2800000.0]) # J / kg
        
    def test_step_without_in_out_loss(self):
        T = self.TES.step(0, 0, 0, 0, 0, 0, 293.15)
        self.assertEqual(T['T_0'],    293.15) # K
        self.assertEqual(T['T_1'],    293.15) # K
        self.assertEqual(T['T_2'],    293.15) # K

    def test_step_loss(self):
        T = self.TES.step(0, 0, 0, 0, 0, 0, 283.15)
        self.assertAlmostEqual(T['T_0'][0],    293.14975714, places=6) # K
        self.assertAlmostEqual(T['T_1'][0],    293.14983905, places=6) # K
        self.assertAlmostEqual(T['T_2'][0],    293.14975714, places=6) # K

    def test_step_HP_input(self):
        T = self.TES.step(5, 5, 0, 0, 313.15, 0, 293.15)
        self.assertAlmostEqual(T['T_0'][0],     300.39735554, places=6) # K
        self.assertAlmostEqual(T['T_1'][0],     294.65876408, places=6) # K
        self.assertAlmostEqual(T['T_2'][0],     293.36758316, places=6) # K, dif
    
    def test_step_DHW_demand(self):
        T = self.TES.step(0, 0, 3, 3, 0, 283.15, 293.15)
        self.assertAlmostEqual(T['T_0'][0],    293.12317183, places=6) # K, dif
        self.assertAlmostEqual(T['T_1'][0],    292.84492359, places=6) # K
        self.assertAlmostEqual(T['T_2'][0],    290.78382239, places=6) # K

    def test_step_HP_input_DHW_demand(self):
        T = self.TES.step(5, 5, 3, 3, 313.15, 283.15, 293.15)
        self.assertAlmostEqual(T['T_0'][0],    300.39735554, places=6) # K
        self.assertAlmostEqual(T['T_1'][0],    293.80935973, places=6) # K
        self.assertAlmostEqual(T['T_2'][0],    291.01302933, places=6) # K, dif
