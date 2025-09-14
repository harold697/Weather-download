import streamlit as st
import io
import datetime
import requests
import zipfile
import geopandas as gpd
import pandas as pd
import zipfile
import tempfile
import geopandas as gpd
import fiona

st.title('Farm Weather Downloader')

uploaded_file = st.file_uploader("Upload a KML or KMZ file containig the farm boundary", 
                                 type=(["kmz"], ["kml"])
                                )

current_year = datetime.datetime.now().year
current_date = datetime.datetime.now()

start_year = st.selectbox("Select first year to download", list(range(2000, current_year + 1)))
end_year = st.selectbox("Select last year to download", list(range(2000, current_year + 1)))

if end_year < start_year:
    st.error("⚠️ End year cannot be less than start year. Please select again.")
    st.stop() 

start_date = f"{start_year}-01-01"

if start_year == current_year and current_date <= datetime.date(current_year, 12, 31):
  end_date = f"{current_date}"
if start_year == current_year and current_date >= datetime.date(current_year, 12, 31):
  end_date = f"{end_year}-12-31"
else:
  end_date = f"{end_year}-12-31"

if uploaded_file is not None:
    if uploaded_file.name.endswith(".kmz"):
        # Extract KMZ (zip) into a temporary folder
        with tempfile.TemporaryDirectory() as tmpdir:
            kmz_path = f"{tmpdir}/{uploaded_file.name}"
            with open(kmz_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with zipfile.ZipFile(kmz_path, "r") as z:
                z.extractall(tmpdir)

            # Find KML inside
            for file in z.namelist():
                if file.endswith(".kml"):
                    kml_path = f"{tmpdir}/{file}"
                    break
    else:
        # Directly save KML
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmpfile:
            tmpfile.write(uploaded_file.getbuffer())
            kml_path = tmpfile.name

    # Load into GeoPandas
    layers = fiona.listlayers(kml_path)
    gdf = gpd.read_file(kml_path, driver="KML", layer=layers[0])
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
        
    st.success("✅ Boundary loaded successfully!")
    st.write(gdf)