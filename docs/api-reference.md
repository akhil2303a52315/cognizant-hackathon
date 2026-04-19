# API Reference for SupplyChainGPT Council

APIs NOT yet integrated in the project, organized by missing segments. Already-integrated segments (Finance/Stocks, Currency/Forex, Economic Data, Weather, News, Social, Commodities, Shipping, Suppliers, Scraping, Security, Knowledge) are excluded.

---

## 🆓 NO API KEY REQUIRED

### 1. Air Quality & Environmental Risk

| API | Description | Link |
|-----|-------------|------|
| **Open-Meteo Air Quality** | Air quality forecasts | https://open-meteo.com/en/docs/air-quality-api |
| **Open-Meteo** | Global weather forecasts | https://open-meteo.com/ |
| **USGS Earthquake API** | Real-time seismic data | https://earthquake.usgs.gov/fdsnws/event/1/ |

### 2. Flight & Air Cargo Tracking

| API | Description | Link |
|-----|-------------|------|
| **OpenSky Network** | Real-time flight data | https://opensky-network.org/apidoc/index.html |

### 3. Geocoding & Supplier Mapping

| API | Description | Link |
|-----|-------------|------|
| **REST Countries** | Country data, flags, currencies, capitals | https://restcountries.com/ |
| **Nominatim** | OpenStreetMap geocoding & reverse geocoding | https://nominatim.org/release-docs/latest/api/Overview/ |
| **ip-api** | IP geolocation (free tier, no key) | https://ip-api.com/docs |
| **GeoJS** | IP geolocation without API key | https://www.geojs.io/ |
| **OpenStreetMap** | Free maps & routing | http://wiki.openstreetmap.org/wiki/API |

### 4. Maritime & Sea Freight

| API | Description | Link |
|-----|-------------|------|
| **OpenSky Network** | Flight + maritime tracking data | https://opensky-network.org/apidoc/index.html |

### 5. VAT & Tax Validation

| API | Description | Link |
|-----|-------------|------|
| **VATComply** | Exchange rates & VAT validation | https://www.vatcomply.com/documentation |

### 6. Government & Open Data

| API | Description | Link |
|-----|-------------|------|
| **OpenCorporates** | Company data (limited free) | http://api.opencorporates.com/documentation/API-Reference |
| **Wikipedia API** | Access Wikipedia content | https://www.mediawiki.org/wiki/API:Main_page |
| **Wikidata** | Structured Wikipedia data | https://www.wikidata.org/w/api.php?action=help |
| **World Bank** | Economic indicators | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-world-bank-apis |
| **European Central Bank** | Euro statistics | https://sdw.ecb.europa.eu/ |

---

## 🔐 API KEY REQUIRED

### 1. Air Quality & Environmental Risk 🔴 High Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **OpenAQ** | Global air quality data | https://docs.openaq.org/ |
| **IQAir** | Air quality & pollution data | https://www.iqair.com/air-pollution-data-api |
| **BreezoMeter** | Pollen & air quality | https://docs.breezometer.com/api-documentation/pollen-api/v2/ |
| **Carbon Interface** | Carbon emissions data | https://docs.carboninterface.com/ |
| **Tomorrow.io** | Weather + climate intelligence | https://app.tomorrow.io/signup |
| **Storm Glass** | Marine weather data | https://stormglass.io/ |
| **OpenUV** | UV index data | https://www.openuv.io/ |

### 2. Flight & Air Cargo Tracking 🔴 High Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **Aviationstack** | Flight data | https://aviationstack.com/signup |
| **Amadeus** | Travel & flight data | https://developers.amadeus.com/register |
| **Open Charge Map** | EV charging stations | https://openchargemap.org/site/develop/api |

### 3. Maritime & Sea Freight 🔴 High Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **MarineTraffic** | Vessel tracking | https://www.marinetraffic.com/en/ais-api-services |
| **AIS Hub** | Vessel AIS data | http://www.aishub.net/api |
| **BIC-Boxtech** | Container database | https://docs.bic-boxtech.org/ |

### 4. Package & Shipment Tracking 🟡 Medium Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **Aftership** | Universal package tracking | https://www.aftership.com/signup |
| **Shippo** | Shipping labels & tracking | https://goshippo.com/signup/ |
| **UPS API** | UPS shipping | https://www.ups.com/upsdeveloperkit |
| **USPS Web Tools** | USPS services | https://registration.shippingapis.com/ |
| **FedEx API** | FedEx shipping | https://www.fedex.com/en-us/developer.html |
| **PostNord** | Nordic shipping | https://developer.postnord.com/api |

### 5. Geocoding & Supplier Mapping 🟡 Medium Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **GeoNames** (full access) | Geographic database | http://www.geonames.org/login |
| **OpenCage** | Forward/reverse geocoding | https://opencagedata.com/users/sign_up |
| **LocationIQ** | Geocoding & maps | https://locationiq.org/#register |
| **Mapbox** | Maps & location | https://account.mapbox.com/auth/signup/ |
| **Google Maps Platform** | Maps, geocoding, routes | https://console.cloud.google.com/freetrial |
| **Here Maps** | Maps & location | https://developer.here.com/sign-up |
| **PositionStack** | Geocoding service | https://positionstack.com/signup |

### 6. IP Geolocation 🟡 Medium Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **IPstack** | IP geolocation | https://ipstack.com/signup/free |
| **IP Geolocation** | IP to location | https://ipgeolocation.io/signup.html |
| **IP2Location** | IP geolocation & proxy | https://www.ip2location.com/web-service/ip2location |
| **Radar** | Geofencing & location | https://radar.io/signup |

### 7. VAT & Tax Validation 🟢 Low Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **VAT Validation (Abstract)** | EU VAT verification | https://www.abstractapi.com/vat-validation-rates-api |

### 8. Address Validation 🟢 Low Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **Lob.com** | Address verification | https://dashboard.lob.com/#/register |
| **Smarty Streets** | US address validation | https://www.smarty.com/products/apis |

### 9. Premium Weather Intelligence 🟢 Low Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **Visual Crossing** | Historical weather data | https://www.visualcrossing.com/weather-api |
| **WeatherAPI** | Real-time weather | https://www.weatherapi.com/signup.aspx |
| **AccuWeather** | Commercial weather data | https://developer.accuweather.com/user/register |

### 10. Government & Open Data 🟢 Low Priority

| API | Description | Get API Key |
|-----|-------------|-------------|
| **NASA APIs** | Space & Earth data | https://api.nasa.gov/ |
| **USDA FoodData Central** | Food & nutrition | https://fdc.nal.usda.gov/api-key-signup.html |
| **FDA Open Data** | Drug & food data | https://open.fda.gov/apis/ |
| **Kaggle** | Datasets & ML | https://www.kaggle.com/account/login?phase=startRegisterTab |

---

## 📊 Free Tier Limits

| API | Free Limit |
|-----|-----------|
| **Open-Meteo** | 10,000 calls/day |
| **Nominatim** | 1 request/second |
| **REST Countries** | No limits |
| **USGS Earthquake** | No limits |
| **OpenSky** | 100 calls/5min |
| **OpenAQ** | 100 calls/min |
| **IQAir** | 1,000 calls/month |
| **Aviationstack** | 100 calls/month |
| **Aftership** | 50 shipments |
| **GeoNames** | 1,000 credits/day |
| **OpenCage** | 2,500 calls/day |
| **LocationIQ** | 5,000 calls/month |
| **Carbon Interface** | 30 calls/month |

---

*Last Updated: April 2026*
