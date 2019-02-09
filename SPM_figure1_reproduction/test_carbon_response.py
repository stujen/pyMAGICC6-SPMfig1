import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt

import pymagicc
from pymagicc import scenarios

# import and clear the RCP26 database and create idealised CO2 emissions timeseries
def empty_scen(index_start=1765,index_end=2500):
	empty_scen = pd.DataFrame(columns=scenarios['RCP26']['WORLD'].columns,index=np.arange(index_start,index_end+1))
	empty_scen['FossilCO2'] = np.zeros(index_end-index_start)
	CO2only_scen = empty_scen['FossilCO2']

	return CO2only_scen

start_year = 0
end_year = 500

pulseCO2_scen = empty_scen()
pulseCO2_scen['FossilCO2'].loc[start_year+100] = 100.0

constCO2_scen = empty_scen()
constCO2_scen['FossilCO2'].loc[start_year:] = 100.0

triangleCO2_scen = empty_scen()
triangleCO2_scen['FossilCO2'].loc[start_year+100:start_year+200] = 0.1 * np.arange(0,100,1)
triangleCO2_scen['FossilCO2'].loc[start_year+200:start_year+300] = 0.1 * np.arange(100,0,-1)

fig, ax = plt.subplots()
pulseCO2_scen['FossilCO2'].plot(ax=ax, color='red')
constCO2_scen['FossilCO2'].plot(ax=ax, color='green')
triangleCO2_scen['FossilCO2'].plot(ax=ax, color='blue')

plt.show()
