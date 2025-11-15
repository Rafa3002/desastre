import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import L from 'leaflet';

// Solucionar iconos de Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Iconos personalizados para diferentes tipos de alerta
const createCustomIcon = (type, severity) => {
  const colors = {
    inundacion: 'blue',
    terremoto: 'red', 
    incendio: 'orange',
    deslizamiento: 'brown',
    general: 'gray'
  };
  
  const color = colors[type] || 'gray';
  
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

// Iconos para refugios
const shelterIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Icono para hospitales
const hospitalIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Icono para selección de ubicación
const selectionIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [35, 51],
  iconAnchor: [17, 51],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Componente para manejar clicks en el mapa
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      onMapClick(lat, lng);
    },
  });
  return null;
}

const MCP_URL = process.env.REACT_APP_MCP_URL || "http://localhost:8001";

export default function MapView({ onLocationSelect, selectedLocation }) {
  const [zones, setZones] = useState([]);
  const [shelters, setShelters] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectionMarker, setSelectionMarker] = useState(null);

  // Referencia para el mapa
  const mapRef = useRef();

  useEffect(() => {
    loadAllData();
    
    // Configurar actualización automática cada 30 segundos
    const interval = setInterval(() => {
      loadAlerts();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Actualizar marcador de selección cuando cambia la ubicación
  useEffect(() => {
    if (selectedLocation) {
      setSelectionMarker(selectedLocation);
    }
  }, [selectedLocation]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadZones(),
        loadShelters(),
        loadAlerts()
      ]);
    } catch (err) {
      console.error('Error cargando datos:', err);
      setError('Error cargando datos del mapa');
    } finally {
      setLoading(false);
    }
  };

  const loadZones = async () => {
    try {
      const response = await axios.get(`${MCP_URL}/mcp/zones`);
      console.log('Zonas cargadas:', response.data);
      setZones(response.data || []);
    } catch (err) {
      console.error('Error cargando zonas:', err);
      setZones([]);
    }
  };

  const loadShelters = async () => {
    try {
      const response = await axios.get(`${MCP_URL}/mcp/shelters`);
      console.log('Refugios cargados:', response.data);
      setShelters(response.data || []);
    } catch (err) {
      console.error('Error cargando refugios:', err);
      setShelters([]);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await axios.get(`${MCP_URL}/mcp/alerts`);
      console.log('Alertas cargadas:', response.data);
      setAlerts(response.data.alerts || []);
    } catch (err) {
      console.error('Error cargando alertas:', err);
      setAlerts([]);
    }
  };

  const handleMapClick = (lat, lng) => {
    console.log(`📍 Map click: ${lat}, ${lng}`);
    setSelectionMarker({ lat, lng });
    
    if (onLocationSelect) {
      onLocationSelect(lat, lng);
    }
  };

  // Estilos para las zonas
  const getZoneStyle = (zone) => {
    const baseStyle = {
      weight: 2,
      opacity: 0.7,
      fillOpacity: 0.3
    };

    switch (zone.zone_type) {
      case 'risk':
        return { ...baseStyle, color: '#ff4444', fillColor: '#ff4444' };
      case 'safe':
        return { ...baseStyle, color: '#44ff44', fillColor: '#44ff44' };
      case 'evacuation':
        return { ...baseStyle, color: '#4444ff', fillColor: '#4444ff' };
      default:
        return { ...baseStyle, color: '#ffaa00', fillColor: '#ffaa00' };
    }
  };

  // Obtener icono para refugio según tipo
  const getShelterIcon = (shelter) => {
    switch (shelter.shelter_type) {
      case 'hospital':
        return hospitalIcon;
      case 'meeting_point':
        return selectionIcon; // Usar icono diferente para puntos de encuentro
      default:
        return shelterIcon;
    }
  };

  if (loading) {
    return (
      <div style={{ 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f8f9fa'
      }}>
        <div>🔄 Cargando mapa...</div>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', position: 'relative' }}>
      {/* Controles del mapa */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 1000,
        background: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.3)',
        maxWidth: '300px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>🗺️ Controles del Mapa</h4>
        
        <div style={{ marginBottom: '10px' }}>
          <strong>📍 Clic en el mapa</strong> para seleccionar ubicación del desastre
        </div>
        
        <button 
          onClick={loadAllData}
          style={{
            padding: '10px 15px',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            width: '100%'
          }}
        >
          🔄 Actualizar Mapa
        </button>

        {selectionMarker && (
          <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
            📍 Seleccionado: {selectionMarker.lat.toFixed(4)}, {selectionMarker.lng.toFixed(4)}
          </div>
        )}
      </div>

      {error && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          zIndex: 1000,
          background: '#f8d7da',
          color: '#721c24',
          padding: '10px',
          borderRadius: '4px',
          border: '1px solid #f5c6cb',
          maxWidth: '300px'
        }}>
          ❌ {error}
        </div>
      )}

      {/* Mapa */}
      <MapContainer
        center={[14.625, -90.525]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <MapClickHandler onMapClick={handleMapClick} />
        
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Zonas de riesgo */}
        {zones.map((zone) => {
          try {
            const geojson = JSON.parse(zone.geojson);
            return (
              <GeoJSON 
                key={zone.id} 
                data={geojson} 
                style={getZoneStyle(zone)}
                onEachFeature={(feature, layer) => {
                  layer.bindPopup(`
                    <div style="min-width: 200px">
                      <strong>${zone.name}</strong><br/>
                      <em>Tipo: ${zone.zone_type === 'risk' ? 'Zona de Riesgo' : 
                                 zone.zone_type === 'safe' ? 'Área Segura' : 
                                 'Zona de Evacuación'}</em>
                    </div>
                  `);
                }}
              />
            );
          } catch (e) {
            console.error('Error parseando GeoJSON:', e);
            return null;
          }
        })}

        {/* Refugios e instituciones */}
        {shelters.map(shelter => (
          <Marker
            key={`shelter-${shelter.id}`}
            position={[shelter.lat, shelter.lon]}
            icon={getShelterIcon(shelter)}
          >
            <Popup>
              <div style={{ minWidth: '200px' }}>
                <strong>
                  {shelter.shelter_type === 'hospital' ? '🏥 ' : 
                   shelter.shelter_type === 'meeting_point' ? '📍 ' : '🏠 '}
                  {shelter.name}
                </strong><br/>
                <em>
                  {shelter.shelter_type === 'hospital' ? 'Hospital' : 
                   shelter.shelter_type === 'meeting_point' ? 'Punto de Encuentro' : 
                   'Refugio'}
                </em><br/>
                Capacidad: {shelter.capacity || 'No especificada'}<br/>
                <small>📞 Contactar para más información</small>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Alertas */}
        {alerts.map(alert => (
          <Marker
            key={`alert-${alert.id}`}
            position={[alert.lat, alert.lon]}
            icon={createCustomIcon(alert.alert_type, alert.severity)}
          >
            <Popup>
              <div style={{ minWidth: '250px' }}>
                <strong>🚨 {alert.title}</strong><br/>
                {alert.description && <>{alert.description}<br/></>}
                <div style={{ margin: '5px 0' }}>
                  <strong>Tipo:</strong> {
                    alert.alert_type === 'inundacion' ? '🌊 Inundación' :
                    alert.alert_type === 'terremoto' ? '🏚️ Terremoto' :
                    alert.alert_type === 'incendio' ? '🔥 Incendio' :
                    alert.alert_type === 'deslizamiento' ? '⛰️ Deslizamiento' :
                    '⚠️ General'
                  }<br/>
                  <strong>Severidad:</strong> {
                    alert.severity === 1 ? '🟢 Baja' : 
                    alert.severity === 2 ? '🟡 Media' : 
                    alert.severity === 3 ? '🔴 Alta' : '🚨 Crítica'
                  }
                </div>
                <small>
                  📅 {new Date(alert.created_at).toLocaleString()}<br/>
                  📍 {alert.lat.toFixed(4)}, {alert.lon.toFixed(4)}
                </small>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Marcador de selección */}
        {selectionMarker && (
          <Marker
            position={[selectionMarker.lat, selectionMarker.lng]}
            icon={selectionIcon}
          >
            <Popup>
              <div style={{ minWidth: '200px' }}>
                <strong>📍 Ubicación Seleccionada</strong><br/>
                <em>Haz clic aquí para crear una alerta</em><br/>
                Lat: {selectionMarker.lat.toFixed(4)}<br/>
                Lng: {selectionMarker.lng.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Leyenda mejorada */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        zIndex: 1000,
        background: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.3)',
        maxWidth: '300px',
        fontSize: '12px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>📖 Leyenda del Mapa</h4>
        
        <div style={{ marginBottom: '8px' }}>
          <strong>🚨 Alertas:</strong>
          <div>🔵 Inundación</div>
          <div>🔴 Terremoto</div>
          <div>🟠 Incendio</div>
          <div>🟤 Deslizamiento</div>
          <div>⚫ General</div>
        </div>

        <div style={{ marginBottom: '8px' }}>
          <strong>🏠 Instituciones:</strong>
          <div>🟢 Refugios</div>
          <div>🔴 Hospitales</div>
          <div>🟣 Puntos de Encuentro</div>
        </div>

        <div style={{ marginBottom: '8px' }}>
          <strong>🗺️ Zonas:</strong>
          <div>🔴 Zonas de Riesgo</div>
          <div>🟢 Áreas Seguras</div>
          <div>🔵 Rutas de Evacuación</div>
        </div>

        <div>
          <strong>📍 Interacción:</strong>
          <div>🟣 Clic para seleccionar ubicación</div>
        </div>
      </div>
    </div>
  );
}