import React, { useState } from 'react';
import MapView from './components/MapView';
import AlertsPanel from './components/AlertsPanel';
import ExternalAlertsPanel from './components/ExternalAlertsPanel';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('internal');
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [recentAlert, setRecentAlert] = useState(null);

  const handleLocationSelect = (lat, lng) => {
    console.log('📍 Ubicación seleccionada en App:', lat, lng);
    setSelectedLocation({ lat, lng });
  };

  const handleAlertCreated = (alert) => {
    console.log('✅ Nueva alerta creada:', alert);
    setRecentAlert(alert);
    // Aquí podrías actualizar el mapa o mostrar notificación
  };

  return (
    <div className="App">
      <div className="app-container">
        
        {/* Sección del Mapa */}
        <div className="map-section">
          <MapView 
            onLocationSelect={handleLocationSelect}
            selectedLocation={selectedLocation}
          />
        </div>

        {/* Panel Lateral */}
        <div className="panel-section">
          
          {/* Encabezado con pestañas */}
          <div className="panel-header">
            <h2>🚨 Sistema de Alertas</h2>
            <div className="tabs-container">
              <button 
                className={`tab-btn ${activeTab === 'internal' ? 'active' : ''}`}
                onClick={() => setActiveTab('internal')}
              >
                📝 Crear Alertas
              </button>
              <button 
                className={`tab-btn ${activeTab === 'external' ? 'active' : ''}`}
                onClick={() => setActiveTab('external')}
              >
                🌐 Fuentes Externas
              </button>
            </div>
          </div>

          {/* Contenido de las pestañas */}
          <div className="tab-content">
            {activeTab === 'internal' && (
              <AlertsPanel 
                selectedLocation={selectedLocation}
                onAlertCreated={handleAlertCreated}
              />
            )}
            {activeTab === 'external' && <ExternalAlertsPanel />}
          </div>

        </div>

      </div>
    </div>
  );
}

export default App;