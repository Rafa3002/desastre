import os
import requests
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
from datetime import datetime, timedelta
import asyncio

app = FastAPI(title="MCP Avanzado - Agente Analítico")

# Configuración
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Opcional para análisis avanzado

class AnalysisRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class RiskAssessment(BaseModel):
    risk_level: str
    confidence: float
    factors: List[str]
    recommendations: List[str]

@app.get("/mcp/health")
async def health():
    return {
        "status": "healthy", 
        "version": "2.0",
        "capabilities": [
            "risk_analysis",
            "pattern_detection", 
            "recommendation_engine",
            "data_aggregation",
            "alert_correlation"
        ]
    }

@app.get("/mcp/analytics/dashboard")
async def get_analytics_dashboard():
    """Dashboard analítico consolidado"""
    async with httpx.AsyncClient() as client:
        # Obtener datos de múltiples fuentes
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=100")
        external_response = await client.get(f"{BACKEND_URL}/external-alerts")
        
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
        external_data = external_response.json() if external_response.status_code == 200 else {"alerts": []}
    
    # Análisis básico
    total_alerts = len(alerts_data)
    external_alerts = len(external_data.get("alerts", []))
    
    # Análisis por severidad
    severity_count = {}
    for alert in alerts_data:
        sev = alert.get('severity', 1)
        severity_count[sev] = severity_count.get(sev, 0) + 1
    
    # Análisis temporal (últimas 24 horas)
    recent_alerts = [
        alert for alert in alerts_data 
        if datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(hours=24)
    ]
    
    return {
        "summary": {
            "total_alerts": total_alerts,
            "external_alerts": external_alerts,
            "recent_24h": len(recent_alerts),
            "avg_severity": sum(alert.get('severity', 1) for alert in alerts_data) / total_alerts if total_alerts > 0 else 0
        },
        "severity_breakdown": severity_count,
        "risk_level": calculate_risk_level(severity_count, len(recent_alerts)),
        "trends": analyze_trends(alerts_data),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/mcp/analysis/risk-assessment")
async def risk_assessment(request: AnalysisRequest):
    """Evaluación de riesgo basada en datos actuales"""
    async with httpx.AsyncClient() as client:
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=50")
        external_response = await client.get(f"{BACKEND_URL}/external-alerts")
        
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
        external_data = external_response.json() if external_response.status_code == 200 else {"alerts": []}
    
    # Análisis de factores de riesgo
    risk_factors = []
    recommendations = []
    
    # Factor 1: Alertas de alta severidad recientes
    high_severity_alerts = [a for a in alerts_data if a.get('severity', 1) >= 3]
    if high_severity_alerts:
        risk_factors.append(f"{len(high_severity_alerts)} alertas de alta severidad activas")
        recommendations.append("Monitorear continuamente las alertas de alta severidad")
    
    # Factor 2: Concentración geográfica
    location_clusters = analyze_location_clusters(alerts_data)
    if location_clusters:
        risk_factors.append(f"Concentración de alertas en {len(location_clusters)} zonas")
        recommendations.append("Evaluar recursos en zonas de alta concentración")
    
    # Factor 3: Alertas externas
    if external_data.get('alerts'):
        risk_factors.append(f"{len(external_data['alerts'])} alertas externas detectadas")
        recommendations.append("Integrar alertas externas al sistema de monitoreo")
    
    # Factor 4: Tendencia temporal
    trend = analyze_trends(alerts_data)
    if trend.get('increasing'):
        risk_factors.append("Tendencia creciente en número de alertas")
        recommendations.append("Aumentar capacidad de respuesta")
    
    # Calcular nivel de riesgo
    risk_score = len(risk_factors) * 0.5 + len(high_severity_alerts) * 0.3
    if risk_score >= 2:
        risk_level = "ALTO"
    elif risk_score >= 1:
        risk_level = "MEDIO" 
    else:
        risk_level = "BAJO"
    
    return RiskAssessment(
        risk_level=risk_level,
        confidence=min(risk_score / 3.0, 1.0),
        factors=risk_factors,
        recommendations=recommendations
    )

@app.get("/mcp/analysis/correlation")
async def analyze_correlations():
    """Detectar correlaciones entre alertas y factores externos"""
    async with httpx.AsyncClient() as client:
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=100")
        external_response = await client.get(f"{BACKEND_URL}/external-alerts")
        
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
        external_data = external_response.json() if external_response.status_code == 200 else {"alerts": []}
    
    correlations = []
    
    # Correlación temporal
    time_patterns = analyze_temporal_patterns(alerts_data)
    if time_patterns:
        correlations.append({
            "type": "temporal",
            "description": f"Patrón temporal detectado: {time_patterns}",
            "confidence": 0.7
        })
    
    # Correlación geográfica
    geo_clusters = analyze_location_clusters(alerts_data)
    if geo_clusters:
        correlations.append({
            "type": "geographic", 
            "description": f"{len(geo_clusters)} clusters geográficos identificados",
            "confidence": 0.8
        })
    
    # Correlación con alertas externas
    if external_data.get('alerts'):
        external_corr = correlate_with_external(alerts_data, external_data['alerts'])
        if external_corr:
            correlations.extend(external_corr)
    
    return {
        "total_correlations": len(correlations),
        "correlations": correlations,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }

@app.post("/mcp/analysis/predict")
async def predict_risk(request: AnalysisRequest):
    """Predecir riesgos futuros basado en datos históricos"""
    async with httpx.AsyncClient() as client:
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=200")
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
    
    # Análisis predictivo simple
    trends = analyze_trends(alerts_data)
    seasonal_patterns = analyze_seasonal_patterns(alerts_data)
    
    predictions = []
    
    if trends.get('increasing'):
        predictions.append({
            "timeframe": "24-48 horas",
            "prediction": "Aumento esperado en número de alertas",
            "confidence": 0.75,
            "basis": "Tendencia histórica creciente"
        })
    
    if seasonal_patterns:
        predictions.append({
            "timeframe": "Próxima semana", 
            "prediction": "Posible patrón estacional",
            "confidence": 0.6,
            "basis": f"Patrón detectado: {seasonal_patterns}"
        })
    
    return {
        "predictions": predictions,
        "based_on_samples": len(alerts_data),
        "timestamp": datetime.utcnow().isoformat()
    }

# Funciones de análisis auxiliares
def calculate_risk_level(severity_count: dict, recent_count: int) -> str:
    total_alerts = sum(severity_count.values())
    if total_alerts == 0:
        return "BAJO"
    
    high_severity = severity_count.get(3, 0) + severity_count.get(4, 0)
    risk_score = (high_severity * 0.6) + (recent_count * 0.4)
    
    if risk_score > 5:
        return "CRÍTICO"
    elif risk_score > 3:
        return "ALTO" 
    elif risk_score > 1:
        return "MEDIO"
    else:
        return "BAJO"

def analyze_trends(alerts_data: List[Dict]) -> Dict[str, Any]:
    if not alerts_data:
        return {"trend": "stable", "increasing": False}
    
    # Agrupar por día
    daily_count = {}
    for alert in alerts_data:
        date = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')).date()
        daily_count[date] = daily_count.get(date, 0) + 1
    
    # Analizar tendencia de los últimos 7 días
    recent_dates = sorted(daily_count.keys())[-7:]
    if len(recent_dates) < 2:
        return {"trend": "insufficient_data", "increasing": False}
    
    recent_counts = [daily_count[date] for date in recent_dates]
    trend = "increasing" if recent_counts[-1] > recent_counts[0] else "decreasing"
    
    return {
        "trend": trend,
        "increasing": trend == "increasing",
        "last_7_days": recent_counts
    }

def analyze_temporal_patterns(alerts_data: List[Dict]) -> str:
    if not alerts_data:
        return ""
    
    # Agrupar por hora del día
    hourly_count = {h: 0 for h in range(24)}
    for alert in alerts_data:
        hour = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')).hour
        hourly_count[hour] += 1
    
    # Encontrar horas pico
    max_hour = max(hourly_count, key=hourly_count.get)
    if hourly_count[max_hour] > len(alerts_data) * 0.2:  # 20% de las alertas en una hora
        return f"Pico de alertas alrededor de las {max_hour}:00"
    
    return ""

def analyze_location_clusters(alerts_data: List[Dict]) -> List[Dict]:
    if not alerts_data:
        return []
    
    # Agrupar alertas por proximidad (simplificado)
    clusters = []
    for alert in alerts_data:
        lat, lon = alert.get('lat', 0), alert.get('lon', 0)
        
        # Buscar cluster cercano
        found_cluster = None
        for cluster in clusters:
            cluster_lat, cluster_lon = cluster['center']
            distance = ((lat - cluster_lat)**2 + (lon - cluster_lon)**2)**0.5
            if distance < 0.01:  # ~1km
                found_cluster = cluster
                break
        
        if found_cluster:
            found_cluster['alerts'].append(alert)
            # Actualizar centro
            alerts_in_cluster = found_cluster['alerts']
            avg_lat = sum(a.get('lat', 0) for a in alerts_in_cluster) / len(alerts_in_cluster)
            avg_lon = sum(a.get('lon', 0) for a in alerts_in_cluster) / len(alerts_in_cluster)
            found_cluster['center'] = (avg_lat, avg_lon)
        else:
            clusters.append({
                'center': (lat, lon),
                'alerts': [alert],
                'count': 1
            })
    
    return [c for c in clusters if len(c['alerts']) > 1]  # Solo clusters con múltiples alertas

def analyze_seasonal_patterns(alerts_data: List[Dict]) -> str:
    if len(alerts_data) < 30:  # Necesitamos suficientes datos
        return ""
    
    # Agrupar por mes
    monthly_count = {}
    for alert in alerts_data:
        month = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')).month
        monthly_count[month] = monthly_count.get(month, 0) + 1
    
    # Buscar patrones estacionales
    if len(monthly_count) >= 3:
        avg = sum(monthly_count.values()) / len(monthly_count)
        high_months = [m for m, count in monthly_count.items() if count > avg * 1.5]
        if high_months:
            return f"Mayor actividad en meses: {high_months}"
    
    return ""

def correlate_with_external(internal_alerts: List[Dict], external_alerts: List[Dict]) -> List[Dict]:
    correlations = []
    
    for ext_alert in external_alerts:
        ext_lat, ext_lon = ext_alert.get('lat', 0), ext_alert.get('lon', 0)
        
        # Buscar alertas internas cercanas
        nearby_internal = [
            alert for alert in internal_alerts
            if ((alert.get('lat', 0) - ext_lat)**2 + (alert.get('lon', 0) - ext_lon)**2)**0.5 < 0.02
        ]
        
        if nearby_internal:
            correlations.append({
                "type": "external_internal",
                "description": f"Alerta externa correlacionada con {len(nearby_internal)} alertas internas",
                "external_source": ext_alert.get('source', 'unknown'),
                "internal_count": len(nearby_internal),
                "confidence": 0.8
            })
    
    return correlations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)