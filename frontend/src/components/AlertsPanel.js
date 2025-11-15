import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AlertsPanel.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

export default function AlertsPanel({ selectedLocation, onAlertCreated }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    lat: 14.625,
    lon: -90.525,
    severity: 2,
    alert_type: 'general'
  });
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showForm, setShowForm] = useState(true);
  const [debugInfo, setDebugInfo] = useState('');

  // Sincronizar con la ubicación seleccionada en el mapa
  useEffect(() => {
    console.log('📍 Selected location updated:', selectedLocation);
    if (selectedLocation) {
      setFormData(prev => ({
        ...prev,
        lat: selectedLocation.lat,
        lon: selectedLocation.lng
      }));
      setDebugInfo(`Ubicación actualizada: ${selectedLocation.lat}, ${selectedLocation.lng}`);
    }
  }, [selectedLocation]);

  // Cargar alertas al iniciar
  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      console.log('🔄 Fetching alerts from:', `${BACKEND_URL}/alerts`);
      const response = await axios.get(`${BACKEND_URL}/alerts?limit=10`);
      console.log('✅ Alertas cargadas:', response.data);
      setAlerts(response.data);
      setDebugInfo(`✅ ${response.data.length} alertas cargadas`);
    } catch (error) {
      console.error('❌ Error cargando alertas:', error);
      const errorMsg = `❌ Error: ${error.response?.status || 'Connection'} - ${error.response?.data?.detail || error.message}`;
      setMessage(errorMsg);
      setDebugInfo(errorMsg);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    console.log(`📝 Input change: ${name} = ${value}`);
    setFormData(prev => ({
      ...prev,
      [name]: name === 'lat' || name === 'lon' ? parseFloat(value) || 0 : 
              name === 'severity' ? parseInt(value) || 1 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setDebugInfo('');

    console.log('🚀 Enviando alerta:', formData);

    // Validación básica
    if (!formData.title.trim()) {
      setMessage('❌ El título es requerido');
      setLoading(false);
      return;
    }

    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        lat: formData.lat,
        lon: formData.lon,
        severity: formData.severity,
        alert_type: formData.alert_type
      };

      console.log('📦 Payload a enviar:', payload);

      const response = await axios.post(`${BACKEND_URL}/alerts`, payload, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });

      console.log('✅ Respuesta del servidor:', response.data);
      
      setMessage('✅ ¡Alerta creada exitosamente! Se enviaron notificaciones por SMS y push.');
      setDebugInfo(`Alerta ID: ${response.data.id} creada`);
      
      // Limpiar formulario
      setFormData({
        title: '',
        description: '',
        lat: selectedLocation?.lat || 14.625,
        lon: selectedLocation?.lng || -90.525,
        severity: 2,
        alert_type: 'general'
      });

      // Recargar alertas
      await fetchAlerts();

      // Notificar al componente padre
      if (onAlertCreated) {
        onAlertCreated(response.data);
      }

    } catch (error) {
      console.error('❌ Error completo:', error);
      
      let errorMessage = '❌ Error creando alerta: ';
      
      if (error.response) {
        // El servidor respondió con un código de error
        errorMessage += `${error.response.status} - ${error.response.data?.detail || 'Error del servidor'}`;
        setDebugInfo(`Response: ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        // La petición fue hecha pero no se recibió respuesta
        errorMessage += 'No se pudo conectar con el servidor';
        setDebugInfo('Request made but no response received');
      } else {
        // Algo pasó al configurar la petición
        errorMessage += error.message;
        setDebugInfo(`Error: ${error.message}`);
      }
      
      setMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const alertTypes = [
    { value: 'general', label: '⚠️ General' },
    { value: 'inundacion', label: '🌊 Inundación' },
    { value: 'terremoto', label: '🏚️ Terremoto' },
    { value: 'incendio', label: '🔥 Incendio' },
    { value: 'deslizamiento', label: '⛰️ Deslizamiento' }
  ];

  const predefinedLocations = [
    { name: "🏙️ Centro", lat: 14.625, lon: -90.525 },
    { name: "⬆️ Norte", lat: 14.65, lon: -90.55 },
    { name: "⬇️ Sur", lat: 14.60, lon: -90.50 }
  ];

  return (
    <div className="alerts-panel-improved">
      
      {/* Header del Panel */}
      <div className="panel-header-improved">
        <div className="header-content">
          <h2>🚨 Alertas Locales</h2>
          <p className="header-subtitle">Sistema de monitoreo en tiempo real</p>
        </div>
      </div>

      {/* Información de Debug */}
      {debugInfo && (
        <div className="debug-info">
          <strong>Debug:</strong> {debugInfo}
        </div>
      )}

      {/* Formulario de Alerta */}
      <div className="form-section-improved">
        <div className="section-header-improved">
          <div className="section-title">
            <span className="section-icon">📝</span>
            <h3>Crear Nueva Alerta</h3>
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="alert-form-improved">
          {message && (
            <div className={`message-improved ${message.includes('❌') ? 'error' : 'success'}`}>
              <span className="message-icon">
                {message.includes('❌') ? '❌' : '✅'}
              </span>
              {message}
            </div>
          )}

          <div className="form-group-improved">
            <label className="form-label">Título de la Alerta *</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="Ej: Inundación en zona central reportada"
              required
              className="form-input"
            />
          </div>

          <div className="form-group-improved">
            <label className="form-label">Descripción</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Describe la situación en detalle..."
              rows="3"
              className="form-textarea"
            />
          </div>

          <div className="form-row-improved">
            <div className="form-group-improved">
              <label className="form-label">Tipo de Emergencia</label>
              <select
                name="alert_type"
                value={formData.alert_type}
                onChange={handleInputChange}
                className="form-select"
              >
                {alertTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group-improved">
              <label className="form-label">Nivel de Severidad</label>
              <select
                name="severity"
                value={formData.severity}
                onChange={handleInputChange}
                className="form-select"
              >
                <option value={1}>🟢 Baja</option>
                <option value={2}>🟡 Media</option>
                <option value={3}>🔴 Alta</option>
                <option value={4}>🚨 Crítica</option>
              </select>
            </div>
          </div>

          <div className="form-group-improved">
            <label className="form-label">Ubicación</label>
            
            <div className="location-presets">
              <span className="presets-label">Ubicaciones rápidas:</span>
              <div className="presets-grid">
                {predefinedLocations.map((loc, index) => (
                  <button
                    key={index}
                    type="button"
                    className="location-preset-btn"
                    onClick={() => {
                      console.log('📍 Location preset selected:', loc);
                      setFormData(prev => ({
                        ...prev,
                        lat: loc.lat,
                        lon: loc.lon
                      }));
                    }}
                  >
                    {loc.name}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="coordinates-display-improved">
              <div className="coordinate-item">
                <span className="coord-label">Latitud:</span>
                <input
                  type="number"
                  step="any"
                  name="lat"
                  value={formData.lat}
                  onChange={handleInputChange}
                  className="coord-input"
                />
              </div>
              <div className="coordinate-item">
                <span className="coord-label">Longitud:</span>
                <input
                  type="number"
                  step="any"
                  name="lon"
                  value={formData.lon}
                  onChange={handleInputChange}
                  className="coord-input"
                />
              </div>
            </div>

            {selectedLocation && (
              <div className="location-hint-improved">
                <span className="hint-icon">📍</span>
                Usando ubicación seleccionada en el mapa: {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
              </div>
            )}
          </div>

          <button 
            type="submit" 
            className="submit-btn-improved"
            disabled={loading || !formData.title.trim()}
          >
            <span className="btn-icon">
              {loading ? '⏳' : '📢'}
            </span>
            {loading ? 'Creando Alerta...' : 'Publicar Alerta'}
          </button>

          <div className="test-buttons">
            <button 
              type="button"
              className="test-btn"
              onClick={() => {
                setFormData({
                  title: 'Prueba - Incendio forestal',
                  description: 'Este es un mensaje de prueba del sistema de alertas',
                  lat: 14.625,
                  lon: -90.525,
                  severity: 3,
                  alert_type: 'incendio'
                });
                setDebugInfo('Formulario llenado con datos de prueba');
              }}
            >
              🧪 Llenar con datos de prueba
            </button>
            
            <button 
              type="button"
              className="test-btn"
              onClick={fetchAlerts}
            >
              🔄 Recargar Alertas
            </button>
          </div>
        </form>
      </div>

      {/* Lista de Alertas Recientes */}
      <div className="alerts-list-improved">
        <div className="list-header-improved">
          <div className="list-title">
            <span className="list-icon">📋</span>
            <h3>Alertas Recientes ({alerts.length})</h3>
          </div>
        </div>

        <div className="alerts-container-improved">
          {alerts.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h4>No hay alertas activas</h4>
              <p>Crea la primera alerta usando el formulario superior</p>
            </div>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} className="alert-item-improved">
                <div className="alert-header-improved">
                  <div className="alert-title-improved">{alert.title}</div>
                  <div className="alert-severity-improved">
                    {alert.severity === 1 ? '🟢' : 
                     alert.severity === 2 ? '🟡' : 
                     alert.severity === 3 ? '🔴' : '🚨'}
                  </div>
                </div>
                <div className="alert-description-improved">
                  {alert.description}
                </div>
                <div className="alert-meta-improved">
                  <span>Tipo: {alert.alert_type}</span>
                  <span>📍 {alert.lat.toFixed(4)}, {alert.lon.toFixed(4)}</span>
                  <span>🕒 {new Date(alert.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}