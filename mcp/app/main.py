import os
import requests
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MCP Avanzado - Sistema de Alertas",
    description="Model Context Protocol con capacidades inteligentes",
    version="2.0.0"
)

# Configuración
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.50:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class AnalysisRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class RiskAssessment(BaseModel):
    risk_level: str
    confidence: float
    factors: List[str]
    recommendations: List[str]

class RecommendationRequest(BaseModel):
    user_role: str
    location: Optional[Dict[str, float]] = None

# Endpoints básicos (compatibilidad)
@app.get("/mcp/health")
def health():
    return {
        "status": "healthy", 
        "version": "2.0.0",
        "capabilities": [
            "analytics",
            "risk_assessment",
            "recommendations",
            "decision_support"
        ]
    }

@app.get("/mcp/alerts")
def mcp_alerts(limit: int = 100):
    try:
        with httpx.Client() as client:
            r = client.get(f"{BACKEND_URL}/alerts?limit={limit}", timeout=10)
            r.raise_for_status()
            alerts = r.json()
            
            # Análisis básico
            counts = {}
            high_severity = 0
            for a in alerts:
                s = str(a.get("severity", 1))
                counts[s] = counts.get(s, 0) + 1
                if a.get('severity', 1) >= 3:
                    high_severity += 1
            
            return {
                "alerts": alerts, 
                "analytics": {
                    "total_alerts": len(alerts),
                    "high_severity_alerts": high_severity,
                    "severity_breakdown": counts,
                    "risk_level": "HIGH" if high_severity > 3 else "MEDIUM" if high_severity > 0 else "LOW"
                }
            }
    except Exception as e:
        logging.error(f"Error en mcp/alerts: {e}")
        return {"alerts": [], "analytics": {"error": str(e)}}

@app.get("/mcp/zones")
def mcp_zones():
    try:
        with httpx.Client() as client:
            r = client.get(f"{BACKEND_URL}/zones", timeout=10)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logging.error(f"Error en mcp/zones: {e}")
        return []

@app.get("/mcp/shelters")
def mcp_shelters():
    try:
        with httpx.Client() as client:
            r = client.get(f"{BACKEND_URL}/shelters", timeout=10)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logging.error(f"Error en mcp/shelters: {e}")
        return []

# 🆕 ENDPOINTS AVANZADOS

@app.get("/mcp/analytics/dashboard")
async def analytics_dashboard():
    """Dashboard analítico completo"""
    try:
        async with httpx.AsyncClient() as client:
            # Obtener datos múltiples
            alerts_task = client.get(f"{BACKEND_URL}/alerts?limit=100")
            external_task = client.get(f"{BACKEND_URL}/external-alerts")
            
            alerts_response, external_response = await asyncio.gather(
                alerts_task, external_task, return_exceptions=True
            )
        
        alerts_data = []
        if not isinstance(alerts_response, Exception) and alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
        
        external_data = {"alerts": []}
        if not isinstance(external_response, Exception) and external_response.status_code == 200:
            external_data = external_response.json()

        # Análisis
        total_alerts = len(alerts_data)
        external_alerts = len(external_data.get("alerts", []))
        
        # Análisis por severidad
        severity_count = {}
        high_severity_count = 0
        for alert in alerts_data:
            sev = alert.get('severity', 1)
            severity_count[sev] = severity_count.get(sev, 0) + 1
            if sev >= 3:
                high_severity_count += 1

        # Alertas recientes (últimas 24 horas)
        recent_alerts = [
            alert for alert in alerts_data 
            if is_recent(alert.get('created_at', ''), hours=24)
        ]

        # Tendencias
        trends = analyze_trends(alerts_data)

        return {
            "summary": {
                "total_alerts": total_alerts,
                "external_alerts": external_alerts,
                "recent_24h": len(recent_alerts),
                "high_severity": high_severity_count,
                "avg_severity": sum(alert.get('severity', 1) for alert in alerts_data) / total_alerts if total_alerts > 0 else 0
            },
            "severity_breakdown": severity_count,
            "risk_assessment": {
                "level": calculate_risk_level(high_severity_count, len(recent_alerts)),
                "factors": get_risk_factors(alerts_data, external_data),
                "confidence": 0.8
            },
            "trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Error en analytics dashboard: {e}")
        return {"error": str(e)}

@app.post("/mcp/analysis/risk-assessment")
async def risk_assessment(request: AnalysisRequest):
    """Evaluación de riesgo inteligente"""
    try:
        async with httpx.AsyncClient() as client:
            alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=50")
            alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []

        # Análisis de factores de riesgo
        risk_factors = []
        recommendations = []

        # Factor 1: Alertas de alta severidad
        high_severity = [a for a in alerts_data if a.get('severity', 1) >= 3]
        if high_severity:
            risk_factors.append(f"{len(high_severity)} alertas de alta severidad activas")
            recommendations.append("Monitorear continuamente alertas críticas")

        # Factor 2: Concentración geográfica
        clusters = analyze_location_clusters(alerts_data)
        if clusters:
            risk_factors.append(f"Concentración en {len(clusters)} zonas de riesgo")
            recommendations.append("Optimizar recursos en zonas críticas")

        # Factor 3: Tendencia temporal
        trends = analyze_trends(alerts_data)
        if trends.get('increasing'):
            risk_factors.append("Tendencia creciente en número de alertas")
            recommendations.append("Preparar capacidad de respuesta adicional")

        # Calcular nivel de riesgo
        risk_score = len(risk_factors) * 0.5 + len(high_severity) * 0.3
        if risk_score >= 2:
            risk_level = "HIGH"
        elif risk_score >= 1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return RiskAssessment(
            risk_level=risk_level,
            confidence=min(risk_score / 3.0, 1.0),
            factors=risk_factors,
            recommendations=recommendations
        )

    except Exception as e:
        logging.error(f"Error en risk assessment: {e}")
        return RiskAssessment(
            risk_level="UNKNOWN",
            confidence=0.0,
            factors=[f"Error: {str(e)}"],
            recommendations=["Revisar conectividad con backend"]
        )

@app.post("/mcp/recommendations/personalized")
async def personalized_recommendations(request: RecommendationRequest):
    """Recomendaciones personalizadas por rol de usuario"""
    try:
        async with httpx.AsyncClient() as client:
            alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=50")
            shelters_response = await client.get(f"{BACKEND_URL}/shelters")
            
            alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
            shelters_data = shelters_response.json() if shelters_response.status_code == 200 else []

        # Generar recomendaciones basadas en rol
        if request.user_role == "first_responder":
            return generate_responder_recommendations(alerts_data, request.location)
        elif request.user_role == "coordinator":
            return generate_coordinator_recommendations(alerts_data)
        elif request.user_role == "citizen":
            return generate_citizen_recommendations(alerts_data, shelters_data, request.location)
        else:
            return generate_general_recommendations(alerts_data)

    except Exception as e:
        logging.error(f"Error en recommendations: {e}")
        return {
            "recommendations": [{
                "type": "error",
                "title": "Error del sistema",
                "description": f"No se pudieron generar recomendaciones: {str(e)}",
                "actions": ["Reintentar más tarde", "Contactar soporte"]
            }],
            "priority": "LOW"
        }

@app.get("/mcp/analysis/correlation")
async def analyze_correlations():
    """Análisis de correlaciones entre alertas"""
    try:
        async with httpx.AsyncClient() as client:
            alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=100")
            alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []

        correlations = []

        # Correlación temporal
        time_patterns = analyze_temporal_patterns(alerts_data)
        if time_patterns:
            correlations.append({
                "type": "temporal",
                "description": time_patterns,
                "confidence": 0.7
            })

        # Correlación geográfica
        clusters = analyze_location_clusters(alerts_data)
        if clusters:
            correlations.append({
                "type": "geographic",
                "description": f"{len(clusters)} clusters geográficos identificados",
                "confidence": 0.8
            })

        return {
            "total_correlations": len(correlations),
            "correlations": correlations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Error en correlation analysis: {e}")
        return {"correlations": [], "error": str(e)}

# 🔧 FUNCIONES AUXILIARES

def is_recent(timestamp: str, hours: int = 24) -> bool:
    """Verificar si una alerta es reciente"""
    try:
        if not timestamp:
            return False
        # Ajustar formato de timestamp
        if timestamp.endswith('Z'):
            timestamp = timestamp.replace('Z', '+00:00')
        alert_time = datetime.fromisoformat(timestamp)
        return datetime.utcnow() - alert_time < timedelta(hours=hours)
    except:
        return False

def analyze_trends(alerts_data: List[Dict]) -> Dict[str, Any]:
    """Analizar tendencias en las alertas"""
    if not alerts_data:
        return {"trend": "stable", "increasing": False}
    
    # Agrupar por fecha
    daily_count = {}
    for alert in alerts_data:
        try:
            date = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')).date()
            daily_count[date] = daily_count.get(date, 0) + 1
        except:
            continue
    
    # Analizar tendencia de últimos días
    recent_dates = sorted(daily_count.keys())[-3:]  # Últimos 3 días
    if len(recent_dates) < 2:
        return {"trend": "insufficient_data", "increasing": False}
    
    recent_counts = [daily_count[date] for date in recent_dates]
    trend = "increasing" if recent_counts[-1] > recent_counts[0] else "decreasing"
    
    return {
        "trend": trend,
        "increasing": trend == "increasing",
        "recent_counts": recent_counts
    }

def calculate_risk_level(high_severity_count: int, recent_count: int) -> str:
    """Calcular nivel de riesgo"""
    risk_score = (high_severity_count * 0.6) + (recent_count * 0.4)
    
    if risk_score > 5:
        return "CRITICAL"
    elif risk_score > 3:
        return "HIGH"
    elif risk_score > 1:
        return "MEDIUM"
    else:
        return "LOW"

def get_risk_factors(alerts_data: List[Dict], external_data: Dict) -> List[str]:
    """Obtener factores de riesgo"""
    factors = []
    
    high_severity = len([a for a in alerts_data if a.get('severity', 1) >= 3])
    if high_severity > 0:
        factors.append(f"{high_severity} alertas de alta severidad")
    
    clusters = analyze_location_clusters(alerts_data)
    if clusters:
        factors.append(f"Concentración en {len(clusters)} zonas")
    
    if external_data.get('alerts'):
        factors.append(f"{len(external_data['alerts'])} alertas externas")
    
    return factors

def analyze_location_clusters(alerts_data: List[Dict]) -> List[Dict]:
    """Analizar clusters geográficos de alertas"""
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
            # Actualizar centro del cluster
            alerts_in_cluster = found_cluster['alerts']
            avg_lat = sum(a.get('lat', 0) for a in alerts_in_cluster) / len(alerts_in_cluster)
            avg_lon = sum(a.get('lon', 0) for a in alerts_in_cluster) / len(alerts_in_cluster)
            found_cluster['center'] = (avg_lat, avg_lon)
            found_cluster['count'] = len(alerts_in_cluster)
        else:
            clusters.append({
                'center': (lat, lon),
                'alerts': [alert],
                'count': 1
            })
    
    return [c for c in clusters if c['count'] > 1]

def analyze_temporal_patterns(alerts_data: List[Dict]) -> str:
    """Analizar patrones temporales"""
    if not alerts_data:
        return ""
    
    # Agrupar por hora del día
    hourly_count = {h: 0 for h in range(24)}
    for alert in alerts_data:
        try:
            hour = datetime.fromisoformat(alert['created_at'].replace('Z', '+00:00')).hour
            hourly_count[hour] += 1
        except:
            continue
    
    # Encontrar horas pico
    max_hour = max(hourly_count, key=hourly_count.get)
    max_count = hourly_count[max_hour]
    total_alerts = len(alerts_data)
    
    if max_count > total_alerts * 0.2:  # 20% en una hora
        return f"Pico de actividad alrededor de las {max_hour}:00"
    
    return ""

# 🎯 FUNCIONES DE RECOMENDACIONES

def generate_responder_recommendations(alerts: List[Dict], location: Optional[Dict]) -> Dict:
    """Recomendaciones para equipos de respuesta"""
    nearby_alerts = get_nearby_alerts(alerts, location) if location else []
    high_priority = [a for a in nearby_alerts if a.get('severity', 1) >= 3]
    
    recommendations = []
    
    if high_priority:
        recommendations.append({
            "type": "immediate_action",
            "title": "Atender alertas críticas",
            "description": f"{len(high_priority)} alertas de alta prioridad en tu área",
            "actions": ["Desplegar equipo", "Reportar situación", "Solicitar apoyo"]
        })
    
    recommendations.append({
        "type": "preparedness",
        "title": "Mantenerse preparado",
        "description": "Equipo listo para respuesta inmediata",
        "actions": ["Verificar equipamiento", "Monitorear comunicaciones", "Coordinar con base"]
    })
    
    return {
        "recommendations": recommendations,
        "priority": "HIGH" if high_priority else "MEDIUM",
        "validity_period": "1h"
    }

def generate_coordinator_recommendations(alerts: List[Dict]) -> Dict:
    """Recomendaciones para coordinadores"""
    high_severity = len([a for a in alerts if a.get('severity', 1) >= 3])
    clusters = analyze_location_clusters(alerts)
    
    recommendations = []
    
    if high_severity > 0:
        recommendations.append({
            "type": "resource_management",
            "title": "Gestionar recursos críticos",
            "description": f"{high_severity} alertas de alta severidad requieren atención",
            "actions": ["Priorizar recursos", "Coordinar equipos", "Actualizar planes"]
        })
    
    if clusters:
        recommendations.append({
            "type": "strategic",
            "title": "Optimizar distribución",
            "description": f"Alertas concentradas en {len(clusters)} zonas",
            "actions": ["Asignar equipos por zona", "Establecer centros locales", "Optimizar rutas"]
        })
    
    return {
        "recommendations": recommendations,
        "priority": "HIGH" if high_severity > 0 else "MEDIUM",
        "validity_period": "2h"
    }

def generate_citizen_recommendations(alerts: List[Dict], shelters: List[Dict], location: Optional[Dict]) -> Dict:
    """Recomendaciones para ciudadanos"""
    nearby_alerts = get_nearby_alerts(alerts, location) if location else []
    nearby_shelters = get_nearby_shelters(shelters, location) if location else []
    
    recommendations = []
    
    if nearby_alerts:
        high_severity_nearby = any(a.get('severity', 1) >= 3 for a in nearby_alerts)
        
        if high_severity_nearby:
            recommendations.append({
                "type": "safety",
                "title": "¡Precaución!",
                "description": "Alertas de alta severidad en tu área",
                "actions": ["Mantente informado", "Sigue instrucciones oficiales", "Prepara kit de emergencia"]
            })
        
        recommendations.append({
            "type": "awareness",
            "title": "Alertas cercanas",
            "description": f"{len(nearby_alerts)} alertas reportadas cerca de ti",
            "actions": ["Monitorea actualizaciones", "Conoce rutas seguras", "Identifica refugios"]
        })
    
    if not recommendations:
        recommendations.append({
            "type": "general",
            "title": "Situación normal",
            "description": "No hay alertas críticas en tu área",
            "actions": ["Mantener preparación básica", "Conocer números de emergencia", "Seguir fuentes oficiales"]
        })
    
    return {
        "recommendations": recommendations,
        "priority": "LOW",
        "validity_period": "6h"
    }

def generate_general_recommendations(alerts: List[Dict]) -> Dict:
    """Recomendaciones generales"""
    return {
        "recommendations": [{
            "type": "general",
            "title": "Monitoreo del sistema",
            "description": f"Sistema activo con {len(alerts)} alertas",
            "actions": ["Revisar dashboard", "Reportar situaciones", "Mantener perfil actualizado"]
        }],
        "priority": "LOW",
        "validity_period": "12h"
    }

def get_nearby_alerts(alerts: List[Dict], location: Dict, max_distance: float = 0.01) -> List[Dict]:
    """Obtener alertas cercanas a una ubicación"""
    if not location:
        return []
    
    lat, lon = location.get('lat', 0), location.get('lon', 0)
    return [
        alert for alert in alerts
        if calculate_distance(lat, lon, alert.get('lat', 0), alert.get('lon', 0)) <= max_distance
    ]

def get_nearby_shelters(shelters: List[Dict], location: Dict, max_distance: float = 0.02) -> List[Dict]:
    """Obtener refugios cercanos a una ubicación"""
    if not location:
        return []
    
    lat, lon = location.get('lat', 0), location.get('lon', 0)
    return [
        shelter for shelter in shelters
        if calculate_distance(lat, lon, shelter.get('lat', 0), shelter.get('lon', 0)) <= max_distance
    ]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcular distancia aproximada entre dos puntos"""
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5

# Necesario para asyncio.gather
import asyncio

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)