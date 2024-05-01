##### head
### Enviornmental variables
- **_id**: Unique identifier for each data entry.
- **date**: Date and time of the recorded data.
- **temperature_2m**(°C): Temperature at 2 meters above ground level in Celsius.
- **relative_humidity_2m**(%): Relative humidity at 2 meters above ground level, expressed as a percentage.
- **dew_point_2m**(°C): Dew point temperature at 2 meters above ground level in Celsius.
- **apparent_temperature**(°C): Perceived temperature, taking into account factors like humidity and wind, in Celsius.
- **precipitation**(mm): Total precipitation in millimeters.
- **rain**(mm): Amount of rainfall in millimeters.
- **snowfall**(cm): Amount of snowfall in centimeter.
- **cloud_cover**(%): Percentage of sky covered by clouds.
- **wind_speed_10m**(km/h): Wind speed at 10 meters above ground level in kilometers per hour.
- **sunshine_duration**(Seconds): Duration of sunshine in seconds.
- **pm10**(μg/m³): Particulate Matter (PM10) concentration in micrograms per cubic meter.
- **pm2_5**(μg/m³): Particulate Matter (PM2.5) concentration in micrograms per cubic meter.
- **carbon_monoxide**(μg/m³): Carbon Monoxide (CO) concentration in micrograms per cubic meter.
- **nitrogen_dioxide**(μg/m³): Nitrogen Dioxide (NO2) concentration in micrograms per cubic meter.
- **sulphur_dioxide**(μg/m³): Sulphur Dioxide (SO2) concentration in micrograms per cubic meter.
- **dust**(μg/m³): Dust concentration in micrograms per cubic meter.
- **european_aqi**: European Air Quality Index (AQI) calculated based on various pollutant concentrations.
- **european_aqi_pm2_5**: European AQI specifically calculated for PM2.5.
- **european_aqi_pm10**: European AQI specifically calculated for PM10.
- **european_aqi_nitrogen_dioxide**: European AQI specifically calculated for nitrogen dioxide (NO2).
- **european_aqi_ozone**: European AQI specifically calculated for ozone (O3).
- **european_aqi_sulphur_dioxide**: European AQI specifically calculated for sulphur dioxide (SO2).


### Counter Locations
- Aston Quay/Fitzgeralds
- ~~Bachelors walk/Bachelors way~~
- Baggot st lower/Wilton tce inbound
- Baggot st upper/Mespil rd/Bank
- Capel st/Mary street
- College Green/Bank Of Ireland
- ~~College Green/Church Lane~~ **loss of data from 5-9th month**
- College st/Westmoreland st
- D'olier st/Burgh Quay
- Dame Street/Londis
- Grafton st/Monsoon
- Grafton Street / Nassau Street / Suffolk Street
- Grafton Street/CompuB
- Grand Canal st upp/Clanwilliam place
- Grand Canal st upp/Clanwilliam place/Google
- ~~Henry Street/Coles Lane/Dunnes~~ **loss of data 5-9month**
- Mary st/Jervis st
- ~~Newcomen Bridge/Charleville mall inbound~~
- ~~Newcomen Bridge/Charleville mall outbound~~
- North Wall Quay/Samuel Beckett bridge East
- North Wall Quay/Samuel Beckett bridge West
- ~~O'Connell St/Parnell St/AIB~~ **5-9 month**
- ~~O'Connell St/Pennys Pedestrian~~ **1-5month**
- O'Connell st/Princes st North
- **Phibsborough Rd/Enniskerry Road** can use this for conclusion
- Richmond st south/Portabello Harbour inbound
- Richmond st south/Portabello Harbour outbound
- ~~Talbot st/Guineys~~
- ~~Westmoreland Street East/Fleet street~~ **loss of data from 9th month**
- ~~Westmoreland Street West/Carrolls~~

locations = [
    "Aston Quay/Fitzgeralds",
    "Baggot st lower/Wilton tce inbound",
    "Baggot st upper/Mespil rd/Bank",
    "Capel st/Mary street",
    "College Green/Bank Of Ireland",
    "College st/Westmoreland st",
    "D'olier st/Burgh Quay",
    "Dame Street/Londis",
    "Grafton st/Monsoon",
    "Grafton Street / Nassau Street / Suffolk Street",
    "Grafton Street/CompuB",
    "Grand Canal st upp/Clanwilliam place",
    "Grand Canal st upp/Clanwilliam place/Google",
    "Mary st/Jervis st",
    "North Wall Quay/Samuel Beckett bridge East",
    "North Wall Quay/Samuel Beckett bridge West",
    "O'Connell st/Princes st North",
    "Phibsborough Rd/Enniskerry Road can use this for conclusion",
    "Richmond st south/Portabello Harbour inbound",
    "Richmond st south/Portabello Harbour outbound"
]

parameters = [
    ["_id"],
    ["date"],
    ["temperature_2m", "°C"],
    ["relative_humidity_2m", "%"],
    ["dew_point_2m", "°C"],
    ["apparent_temperature", "°C"],
    ["precipitation", "mm"],
    ["rain", "mm"],
    ["snowfall", "cm"],
    ["cloud_cover", "%"],
    ["wind_speed_10m", "km/h"],
    ["sunshine_duration", "Seconds"],
    ["pm10", "μg/m³"],
    ["pm2_5", "μg/m³"],
    ["carbon_monoxide", "μg/m³"],
    ["nitrogen_dioxide", "μg/m³"],
    ["sulphur_dioxide", "μg/m³"],
    ["dust", "μg/m³"],
    ["european_aqi"],
    ["european_aqi_pm2_5"],
    ["european_aqi_pm10"],
    ["european_aqi_nitrogen_dioxide"],
    ["european_aqi_ozone"],
    ["european_aqi_sulphur_dioxide"]
]