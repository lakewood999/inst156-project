from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import os

DATA_DIR = 'data'

def load_data(locations):
    locations['fname_loc_string'] = locations['Lat Lon String'].apply(lambda x: x.replace(",", "_"))
    dust_data = pd.DataFrame()
    for index, row in locations.iterrows():
        fname = os.path.join(DATA_DIR, f"g4.areaAvgTimeSeries.M2TMNXAER_5_12_4_DUCMASS.20000201-20250228.{row['fname_loc_string']}.csv")
        if os.path.exists(fname):
            data = pd.read_csv(fname, skiprows=8)
            data['city'] = row['City']
            data['source'] = row['fname_loc_string']
            dust_data = pd.concat([dust_data, data], ignore_index=True)
    # Convert time column to date (we only need month and year)
    dust_data['time'] = pd.to_datetime(dust_data['time'], format='%Y-%m-%d %H:%M:%S')
    # convert from kg/m2 to g/m2; space is needed in the column name
    dust_data['dust_column_mass_density'] = dust_data[' mean_M2TMNXAER_5_12_4_DUCMASS'] * 1000

    aod_data = pd.DataFrame()
    for index, row in locations.iterrows():
        fname = os.path.join(DATA_DIR, f"g4.areaAvgTimeSeries.MOD08_M3_6_1_Deep_Blue_Aerosol_Optical_Depth_550_Land_Mean_Mean.20000201-20250228.{row['fname_loc_string']}.csv")
        if os.path.exists(fname):
            data = pd.read_csv(fname, skiprows=8)
            data['city'] = row['City']
            data['source'] = row['fname_loc_string']
            aod_data = pd.concat([aod_data, data], ignore_index=True)
    # Convert time column to date (we only need month and year)
    aod_data['time'] = pd.to_datetime(aod_data['time'], format='%Y-%m-%d %H:%M:%S')
    aod_data['aod'] = aod_data[' MOD08_M3_6_1_Deep_Blue_Aerosol_Optical_Depth_550_Land_Mean_Mean']

    return dust_data, aod_data

def main():
    # Locations
    locations = pd.read_csv(os.path.join(DATA_DIR, 'Locations.csv'))
    #print(locations.head())

    # Iran bounding box coordinates
    ll_lon, ur_lon, ll_lat, ur_lat = 42, 65, 20, 41
    m = Basemap(projection='merc', lon_0=0, resolution='l',
                llcrnrlon = ll_lon, urcrnrlon = ur_lon,
                llcrnrlat = ll_lat, urcrnrlat = ur_lat,
                epsg=3857 # Mercator
               )
    m.shadedrelief()
    #m.arcgisimage(service='ESRI_Imagery_World_2D', xpixels = 1500, verbose= True)
    m.drawcountries(color='#ffffff', linewidth=0.5)
    m.fillcontinents(color='#c0c0c0', lake_color='#ffffff')

    # Run through each row and plot box
    for index, row in locations.iterrows():
        x1, y1 = m(row['Left Lon'], row['Left Lat'])
        x2, y2 = m(row['Right Lon'], row['Left Lat'])
        x3, y3 = m(row['Right Lon'], row['Right Lat'])
        x4, y4 = m(row['Left Lon'], row['Right Lat'])
        poly = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)],
                       edgecolor='green', linewidth=1, facecolor='none')
        plt.gca().add_patch(poly)

    # Save the map to a file
    plt.savefig('areas_of_interest.png', dpi=300, bbox_inches='tight')

    # Load and process data
    dust_data, aod_data = load_data(locations)

    # Merge dust and AOD data by time and city
    merged_data = pd.merge(dust_data, aod_data, on=['time', 'city', 'source'])
    #print(merged_data.head())
    #print(merged_data.columns)

    # Replicate figure one
    # Select cities: Ahwaz, Bushehr, and Bandar Abbas
    subset = merged_data[merged_data['city'].isin(['Ahwaz', 'Bushehr', 'Bandar Abbas'])]
    # Select months between March 2000 and December 2015
    subset = subset[(subset['time'] >= '2000-03-01') & (subset['time'] <= '2015-12-31')]
    print(subset.head())
    figs, axs = plt.subplots(ncols=2, nrows=3, figsize=(12, 8), dpi=300)
    cities = ['Ahwaz', 'Bushehr', 'Bandar Abbas']
    #aod_lims = [(0, 1.2), (0, 0.7), (0, 0.5)]
    aod_lims = [(0, 1.2), (0, 1.0), (0, 1.0)]
    dust_lims = [(0, 1.4), (0, 1.0), (0, 1.0)]
    #aod_tick_intervals = [0.2, 0.1, 0.1]
    aod_tick_intervals = [0.2, 0.2, 0.2]
    dust_tick_intervals = [0.2, 0.2, 0.2]
    for i, city in enumerate(cities):
        # Plot AOD
        sns.lineplot(data=subset[subset['city'] == city], x='time', y='aod', ax=axs[i, 0], color="black", marker='o',
                     markersize=5, linewidth=0.5)
        # Plot dust column mass density
        ax2 = axs[i, 0].twinx()
        sns.lineplot(data=subset[subset['city'] == city], x='time', y='dust_column_mass_density', ax=ax2,
                     color='blue', marker='o', markersize=5, linewidth=0.5)
        axs[i, 0].set_title(city)
        axs[i, 0].set_ylabel('AOD')
        ax2.set_ylabel('Dust Column Mass Density (g/m2)')
        ax2.yaxis.label.set_color('blue')
        # Set the separate limits
        axs[i, 0].set_ylim(aod_lims[i])
        ax2.set_ylim(dust_lims[i])
        #axs[i, 0].yaxis.set_ticks([x / 10 for x in range(int(aod_lims[i][0] * 10), int(aod_lims[i][1] * 10) + 1, int(aod_tick_intervals[i] * 10))])
        #ax2.yaxis.set_ticks([x / 10 for x in range(int(dust_lims[i][0] * 10), int(dust_lims[i][1] * 10) + 1, int(dust_tick_intervals[i] * 10))])
        # Set the separate tick intervals
        axs[i, 0].yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=int((aod_lims[i][1] - aod_lims[i][0]) // aod_tick_intervals[i]) + 2))
        ax2.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=int((dust_lims[i][1] - dust_lims[i][0]) // dust_tick_intervals[i]) + 2))

        # Right side is a scatter plot
        sns.scatterplot(data=subset[subset['city'] == city], y='dust_column_mass_density', x='aod', ax=axs[i, 1],
                        color='red', s=5)
        # Add trendline
        sns.regplot(data=subset[subset['city'] == city], y='dust_column_mass_density', x='aod', ax=axs[i, 1],
                    scatter=False, color='red', line_kws={'color': 'black', 'linewidth':0.5}, ci=None)
        # Compute pearson correlation and write it on the plot
        corr = subset[subset['city'] == city]['dust_column_mass_density'].corr(subset[subset['city'] == city]['aod'])
        axs[i, 1].text(0.05, 0.95, f'r = {corr:.2f}', transform=axs[i, 1].transAxes,
                       fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))
        axs[i, 1].set_ylim(dust_lims[i])
        axs[i, 1].set_xlim(aod_lims[i])
        axs[i, 1].xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=int((aod_lims[i][1] - aod_lims[i][0]) // aod_tick_intervals[i]) + 2))
        axs[i, 1].yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=int((dust_lims[i][1] - dust_lims[i][0]) // dust_tick_intervals[i]) + 2))
        axs[i, 1].set_xlabel('AOD')
        axs[i, 1].set_ylabel('')
    figs.tight_layout()
    # Save
    plt.savefig('dust_aod_time_series.png', dpi=300)
    
if __name__ == "__main__":
    main()
