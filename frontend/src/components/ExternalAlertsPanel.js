import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ExternalAlertsPanel.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

export default function ExternalAlertsPanel() {
  const [externalAlerts, setExternalAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchExternalAlerts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/external-alerts`);
      if (response.data.success) {
        setExternalAlerts(response.data.alerts || []);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error cargando alertas externas:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExternalAlerts();
    const interval = setInterval(fetchExternalAlerts, 300000);
    return () => clearInterval(interval);
  }, []);

  const getSourceIcon = (source) => {
    const icons = {
      'OPENWEATHER': '🌤️',
      'OPEN_METEO': '🌡️',
      'GDACS': '🌍',
      'NASA_POWER': '🚀'
    };
    return icons[source] || '🔍';
  };

  return (
    <div className="external-panel-compact">
      
      {/* Encabezado con controles */}
      <div className="external-header">
        <div className="external-info">
          <h4>🌐 Fuentes Externas</h4>
          {lastUpdate && (
            <span className="update-time">Actualizado: {lastUpdate}</span>
          )}
        </div>
        <button 
          onClick={fetchExternalAlerts} 
          className="external-refresh"
          disabled={loading}
        >
          {loading ? '⏳' : '🔄'}
        </button>
      </div>

      {/* Resumen rápido */}
      <div className="sources-summary-compact">
        <div className="sources-stats">
          {['OPEN_METEO', 'GDACS', 'OPENWEATHER'].map(source => {
            const count = externalAlerts.filter(a => a.source === source).length;
            return (
              <div key={source} className="source-stat">
                <span className="source-icon">{getSourceIcon(source)}</span>
                <span className="stat-count">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Lista de alertas */}
      <div className="external-alerts-compact">
        <div className="alerts-count">
          {externalAlerts.length} alerta(s) detectada(s)
        </div>
        
        <div className="external-list-container">
          {loading && (
            <div className="external-loading">
              <div className="loading-spinner"></div>
              Buscando alertas...
            </div>
          )}

          {!loading && externalAlerts.length === 0 && (
            <div className="no-external-alerts-compact">
              ✅ No hay alertas externas
            </div>
          )}

          {externalAlerts.map((alert, index) => (
            <div key={index} className="external-alert-compact">
              <div className="external-alert-header">
                <span className="alert-source-badge">
                  {getSourceIcon(alert.source)} {alert.source}
                </span>
                <span className={`alert-severity-badge severity-${alert.severity}`}>
                  Nvl {alert.severity}
                </span>
              </div>
              <div className="external-alert-title">{alert.title}</div>
              <div className="external-alert-desc">{alert.description}</div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}