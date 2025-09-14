import datetime
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def open_meteo_data(paddock,start_date,end_date):
  
  cent = paddock.centroid.iloc[0]

  meteo_url = "https://archive-api.open-meteo.com/v1/archive"
  # Parameters for the API request
  params = {
    'latitude': cent.y,
    'longitude': cent.x,
    'start_date': start_date,
    'end_date': end_date,
    'daily': 'temperature_2m_max,precipitation_sum,temperature_2m_min',
    'timezone': 'auto'
    }

  # Send the request
  r = requests.get(meteo_url, params=params)

  # Check if successful
  if r.status_code == 200:
    try:
      weather_data = r.json()
      date = weather_data["daily"]["time"]
      max_temp = weather_data["daily"]["temperature_2m_max"]
      min_temp = weather_data["daily"]["temperature_2m_min"]
      precipitation = weather_data["daily"]["precipitation_sum"]

      #create df
      df = pd.DataFrame({"date": date,
                        "max_temp": max_temp,
                        "min_temp": min_temp,
                        "precipitation": precipitation
                        })

      df['date'] = pd.to_datetime(df['date'])
      df.set_index('date', inplace=True)
      # GSR rainfall
      df['Year'] = df.index.year
      df['month'] = df.index.month

      # Select Apr 1 to Sep 30 (inclusive)
      mask = (df['month'] >= 4) & (df['month'] <= 9)
      growing_season_rain = (
          df.loc[mask]
          .groupby('Year')['precipitation']
          .sum()
          .rename("Growing Season Rainfall")
      )

      #convert to yearly
      yearly_df = df.resample('YE').agg({
        'max_temp': 'mean',
        'min_temp': 'mean',
        'precipitation': 'sum'
      })

      #Rename columns
      yearly_df.rename(columns={
        'max_temp': 'Average Maximum Temp',
        'min_temp': 'Average Minimum Temp',
        'precipitation': 'Yearly Rainfall'
      }, inplace=True)

      yearly_df.reset_index(inplace=True)

      yearly_df['date'] = yearly_df['date'].dt.year
      yearly_df.rename(columns={'date': 'Year'}, inplace=True)

      yearly_df = yearly_df.merge(
          growing_season_rain, 
          left_on="Year", 
          right_index=True, 
          how="left"
      )

      yearly_df = yearly_df.round(2)

      yearly_df['Year'] = yearly_df['Year'].astype(str)
      avg_row = yearly_df.drop(columns=['Year']).mean(numeric_only=True).round(2)
      
      avg_row['Year'] = 'Average'
      yearly_df = pd.concat([yearly_df, avg_row.to_frame().T], ignore_index=True)

      print("Weather downloaded")
      return yearly_df
    except ValueError:
      print(f"Error processing JSON data: {ValueError}")
      print(r.text)
      return None
  else:
    print(f"Failed to retrieve data: {r.status_code}")