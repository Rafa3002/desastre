import os
import requests
import logging
from datetime import datetime, timedelta
from sqlmodel import Session
from .models import Alert
import json

# Configuración
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GDACS_URL = "https://www.gdacs.org/gdacsapi/api/events/get/eventlist/SEARCH"

class ExternalDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30

    def fetch_weather_alerts(self, lat=14.625, lon=-90.525):
        """Obtener alertas meteorológicas de OpenWeatherMap"""
        try:
            if not OPENWEATHER_API_KEY:
                logging.warning("OpenWeather API key no configurada")
                return None

            # Obtener datos actuales
            current_url = f"{OPENWEATHER_BASE_URL}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es'
            }
            
            response = self.session.get(current_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            
            # Verificar condiciones extremas
            weather_main = data['weather'][0]['main']
            temp = data['main']['temp']
            wind_speed = data['wind']['speed']
            humidity = data['main']['humidity']
            
            # Generar alertas basadas en condiciones
            if weather_main in ['Thunderstorm', 'Hurricane', 'Tornado']:
                alerts.append({
                    'title': f'Alerta Meteorológica: {weather_main}',
                    'description': f'Condición climática severa detectada. {weather_main} en la zona.',
                    'severity': 4,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPENWEATHER'
                })
            
            if temp > 35:  # Temperatura muy alta
                alerts.append({
                    'title': 'Alerta de Temperatura Extrema',
                    'description': f'Temperatura muy alta: {temp}°C. Riesgo de incendios forestales.',
                    'severity': 3,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPENWEATHER'
                })
            
            if wind_speed > 15:  # Vientos fuertes
                alerts.append({
                    'title': 'Alerta de Vientos Fuertes',
                    'description': f'Vientos de {wind_speed} m/s detectados. Posibles daños.',
                    'severity': 3,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPENWEATHER'
                })
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error obteniendo datos de OpenWeather: {e}")
            return None

    def fetch_open_meteo_data(self, lat=14.625, lon=-90.525):
        """Obtener datos meteorológicos de Open-Meteo (sin API key)"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m',
                'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max',
                'timezone': 'auto',
                'forecast_days': 3
            }
            
            response = self.session.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            current = data.get('current', {})
            daily = data.get('daily', {})
            
            # Analizar datos actuales
            precipitation = current.get('precipitation', 0)
            wind_speed = current.get('wind_speed_10m', 0)
            weather_code = current.get('weather_code', 0)
            
            # Generar alertas basadas en códigos de clima
            severe_weather_codes = [95, 96, 99]  # Tormentas severas
            if weather_code in severe_weather_codes:
                alerts.append({
                    'title': 'Alerta de Tormenta Severa',
                    'description': 'Tormenta eléctrica severa detectada en el área.',
                    'severity': 4,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPEN_METEO'
                })
            
            if precipitation > 20:  # Lluvia intensa
                alerts.append({
                    'title': 'Alerta de Lluvia Intensa',
                    'description': f'Precipitación intensa detectada: {precipitation} mm. Riesgo de inundaciones.',
                    'severity': 3,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPEN_METEO'
                })
            
            # Verificar pronóstico para los próximos días
            daily_precipitation = daily.get('precipitation_sum', [])
            if daily_precipitation and max(daily_precipitation) > 30:
                alerts.append({
                    'title': 'Alerta de Lluvias Futuras',
                    'description': 'Se pronostican lluvias intensas en los próximos días.',
                    'severity': 2,
                    'lat': lat,
                    'lon': lon,
                    'source': 'OPEN_METEO'
                })
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error obteniendo datos de Open-Meteo: {e}")
            return None

    def fetch_gdacs_alerts(self):
        """Obtener alertas globales de desastres de GDACS"""
        try:
            params = {
                'fromdate': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'todate': datetime.now().strftime('%Y-%m-%d'),
                'alertlevel': 'Green,Orange,Red',
                'country': 'GT'  # Guatemala
            }
            
            response = self.session.get(GDACS_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            
            for event in data.get('features', []):
                properties = event.get('properties', {})
                geometry = event.get('geometry', {})
                
                event_type = properties.get('eventtype', '')
                alert_level = properties.get('alertlevel', '')
                title = properties.get('title', '')
                description = properties.get('description', '')
                
                # Convertir alert level a severidad numérica
                severity_map = {'Green': 2, 'Orange': 3, 'Red': 4}
                severity = severity_map.get(alert_level, 2)
                
                # Obtener coordenadas (usar el primer punto si es Polygon)
                coords = geometry.get('coordinates', [])
                if coords and isinstance(coords[0], list) and isinstance(coords[0][0], list):
                    # Es un polígono, usar el primer punto
                    lon, lat = coords[0][0]
                else:
                    # Usar coordenadas por defecto de Guatemala
                    lat, lon = 14.625, -90.525
                
                alerts.append({
                    'title': f'GDACS: {title}',
                    'description': description,
                    'severity': severity,
                    'lat': lat,
                    'lon': lon,
                    'source': 'GDACS'
                })
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error obteniendo datos de GDACS: {e}")
            return None

    def fetch_nasa_power_data(self, lat=14.625, lon=-90.525):
        """Obtener datos climáticos de NASA POWER"""
        try:
            url = "https://power.larc.nasa.gov/api/temporal/daily/point"
            params = {
                'parameters': 'T2M,PRECTOT,WS2M,RH2M',
                'start': (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                'end': datetime.now().strftime('%Y%m%d'),
                'latitude': lat,
                'longitude': lon,
                'community': 'AG',
                'format': 'JSON'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Analizar datos para tendencias peligrosas
            temperatures = data.get('properties', {}).get('parameter', {}).get('T2M', {})
            precipitation = data.get('properties', {}).get('parameter', {}).get('PRECTOT', {})
            
            alerts = []
            
            # Verificar temperaturas extremas recientes
            if temperatures:
                avg_temp = sum(temperatures.values()) / len(temperatures)
                if avg_temp > 30:
                    alerts.append({
                        'title': 'Tendencia de Temperaturas Altas',
                        'description': f'Temperatura promedio alta detectada: {avg_temp:.1f}°C',
                        'severity': 2,
                        'lat': lat,
                        'lon': lon,
                        'source': 'NASA_POWER'
                    })
            
            return alerts
            
        except Exception as e:
            logging.error(f"Error obteniendo datos de NASA POWER: {e}")
            return None

    def check_all_sources(self):
        """Verificar todas las fuentes de datos externas"""
        all_alerts = []
        
        try:
            # Open-Meteo (siempre disponible)
            meteo_alerts = self.fetch_open_meteo_data()
            if meteo_alerts:
                all_alerts.extend(meteo_alerts)
            
            # OpenWeatherMap (si tiene API key)
            if OPENWEATHER_API_KEY:
                weather_alerts = self.fetch_weather_alerts()
                if weather_alerts:
                    all_alerts.extend(weather_alerts)
            
            # GDACS Alertas globales
            gdacs_alerts = self.fetch_gdacs_alerts()
            if gdacs_alerts:
                all_alerts.extend(gdacs_alerts)
            
            # NASA POWER datos históricos
            nasa_alerts = self.fetch_nasa_power_data()
            if nasa_alerts:
                all_alerts.extend(nasa_alerts)
                
        except Exception as e:
            logging.error(f"Error general en check_all_sources: {e}")
        
        return all_alerts

# Instancia global
external_fetcher = ExternalDataFetcher()