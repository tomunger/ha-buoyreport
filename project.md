# Project

Write code that will display data from ocean buoys in home assistant.  The goal is to provide a human readable 
display of data from several buoys in the local area.  The list of buoys will likeliy be from 3 to 10, but 
could be longer.  


# Buoy Data Source. 

Data comes from the National Data Buoy Center at: https://www.ndbc.noaa.gov

Each buoy has a station ID.  Data for each buoy can be fetched in different
formats.  

- Full web page with current conditions and historical conditions
  - URL:  ttps://www.ndbc.noaa.gov/station_page.php?station=<station_id>
- Latest observations as a text file
  - URL:  https://www.ndbc.noaa.gov/data/latest_obs/<station_id>.txt
- Latest observations as a RSS
  - URL:  https://www.ndbc.noaa.gov/data/latest_obs/<station_id>.rss


However, the set of observations available for each buoy is not consistent.  
These are the observations I'm most interested in:

- Station name
- Station location in lat lon 
- Local time of the observation
- Wind speed, direction, and gusts
- Air temperature, pressure
- Swell height, period, direction
- Significant swell height
- Wind wave height, period, direction


Here are some sample buoys:


- Station 46206
  - URL:  https://www.ndbc.noaa.gov/station_page.php?station=46206
  - Latest:  https://www.ndbc.noaa.gov/data/latest_obs/46206.txt
  - RSS:  https://www.ndbc.noaa.gov/data/latest_obs/46206.rss
  - Name "La Perouse Bank"
- Station 46087
  - URL:  https://www.ndbc.noaa.gov/station_page.php?station=46087
  - Latest:  https://www.ndbc.noaa.gov/data/latest_obs/46087.txt
  - RSS:  https://www.ndbc.noaa.gov/data/latest_obs/46087.rss
  - Name "Cape Flattery"
- Station neaw1
  - URL:  https://www.ndbc.noaa.gov/station_page.php?station=neaw1
  - Latest:  https://www.ndbc.noaa.gov/data/latest_obs/neaw1.txt
  - RSS:  https://www.ndbc.noaa.gov/data/latest_obs/neaw1.rss
  - Name: "Neah Bay, WA"
- Station 46119
  - URL:  https://www.ndbc.noaa.gov/station_page.php?station=46119
  - Latest:  https://www.ndbc.noaa.gov/data/latest_obs/46119.txt
  - RSS:  https://www.ndbc.noaa.gov/data/latest_obs/46119.rss
  - Name "La Push, 10nm"
- Station 46041
  - URL:  https://www.ndbc.noaa.gov/station_page.php?station=46041
  - Latest:  https://www.ndbc.noaa.gov/data/latest_obs/46041.txt
  - RSS:  https://www.ndbc.noaa.gov/data/latest_obs/46041.rss
  - Name: "Cape Elizabeth"

# User interface

I'm unfamiliar with the homeassistant user inface components.  I believe this should be
a card that can be placed on a page with other weather data.  Is this the correct abstraction to use?

Each card should be configurable with the station ID it is to display.  Should there be one station ID
per card or a list of station ID?

