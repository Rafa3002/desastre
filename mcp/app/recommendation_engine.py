from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import httpx

router = APIRouter(prefix="/mcp/recommendations", tags=["recommendations"])

class RecommendationRequest(BaseModel):
    user_role: str  # "first_responder", "coordinator", "civil_protection", "citizen"
    location: Dict[str, float] = None  # {lat, lon}
    context: Dict[str, Any] = {}

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    priority: str
    validity_period: str

@router.post("/personalized", response_model=RecommendationResponse)
async def get_personalized_recommendations(request: RecommendationRequest):
    """Recomendaciones personalizadas basadas en rol y ubicación"""
    
    async with httpx.AsyncClient() as client:
        # Obtener datos relevantes
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=50")
        external_response = await client.get(f"{BACKEND_URL}/external-alerts")
        shelters_response = await client.get(f"{BACKEND_URL}/shelters")
        
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
        external_data = external_response.json() if external_response.status_code == 200 else {"alerts": []}
        shelters_data = shelters_response.json() if shelters_response.status_code == 200 else []
    
    # Generar recomendaciones basadas en el rol
    if request.user_role == "first_responder":
        return generate_responder_recommendations(alerts_data, request.location)
    elif request.user_role == "coordinator":
        return generate_coordinator_recommendations(alerts_data, external_data.get("alerts", []))
    elif request.user_role == "civil_protection":
        return generate_civil_protection_recommendations(alerts_data, shelters_data)
    elif request.user_role == "citizen":
        return generate_citizen_recommendations(alerts_data, shelters_data, request.location)
    else:
        return generate_general_recommendations(alerts_data)

def generate_responder_recommendations(alerts: List[Dict], location: Dict) -> RecommendationResponse:
    """Recomendaciones para equipos de primera respuesta"""
    nearby_alerts = get_nearby_alerts(alerts, location, max_distance=0.02)
    high_priority = [a for a in nearby_alerts if a.get('severity', 1) >= 3]
    
    recommendations = []
    
    if high_priority:
        recommendations.append({
            "type": "immediate_action",
            "title": "Atender alertas de alta prioridad",
            "description": f"{len(high_priority)} alertas críticas en tu área inmediata",
            "actions": ["Desplegar equipo", "Reportar situación", "Solicitar apoyo si es necesario"]
        })
    
    if nearby_alerts:
        recommendations.append({
            "type": "assessment",
            "title": "Evaluar situación general",
            "description": f"Total de {len(nearby_alerts)} alertas en zona de cobertura",
            "actions": ["Priorizar por severidad", "Coordinar con otros equipos", "Reportar avances"]
        })
    
    # Recomendación de seguridad
    recommendations.append({
        "type": "safety",
        "title": "Protocolos de seguridad",
        "description": "Mantener protocolos de seguridad personal durante intervenciones",
        "actions": ["Equipo de protección completo", "Comunicación constante", "Evaluar riesgos ambientales"]
    })
    
    priority = "HIGH" if high_priority else "MEDIUM"
    
    return RecommendationResponse(
        recommendations=recommendations,
        priority=priority,
        validity_period="1h"
    )

def generate_coordinator_recommendations(internal_alerts: List[Dict], external_alerts: List[Dict]) -> RecommendationResponse:
    """Recomendaciones para coordinadores"""
    recommendations = []
    
    total_alerts = len(internal_alerts)
    high_severity = len([a for a in internal_alerts if a.get('severity', 1) >= 3])
    
    if high_severity > 0:
        recommendations.append({
            "type": "resource_management",
            "title": "Gestionar recursos críticos",
            "description": f"{high_severity} alertas de alta severidad requieren atención prioritaria",
            "actions": ["Movilizar equipos especializados", "Coordinar con autoridades", "Actualizar planes de contingencia"]
        })
    
    if external_alerts:
        recommendations.append({
            "type": "integration",
            "title": "Integrar alertas externas",
            "description": f"{len(external_alerts)} alertas externas detectadas que pueden afectar operaciones",
            "actions": ["Evaluar impacto local", "Actualizar planes de respuesta", "Comunicar a equipos relevantes"]
        })
    
    # Recomendación estratégica
    clusters = analyze_location_clusters(internal_alerts)
    if len(clusters) > 1:
        recommendations.append({
            "type": "strategic",
            "title": "Optimizar distribución de recursos",
            "description": f"Alertas concentradas en {len(clusters)} zonas geográficas",
            "actions": ["Asignar equipos por zona", "Establecer centros de operaciones locales", "Optimizar rutas de respuesta"]
        })
    
    return RecommendationResponse(
        recommendations=recommendations,
        priority="HIGH" if high_severity > 0 else "MEDIUM",
        validity_period="2h"
    )

def generate_civil_protection_recommendations(alerts: List[Dict], shelters: List[Dict]) -> RecommendationResponse:
    """Recomendaciones para protección civil"""
    recommendations = []
    
    # Análisis de capacidad de refugios
    total_shelter_capacity = sum(s.get('capacity', 0) for s in shelters)
    active_alerts = len([a for a in alerts if a.get('severity', 1) >= 2])
    
    if active_alerts > total_shelter_capacity * 0.5:
        recommendations.append({
            "type": "capacity",
            "title": "Ampliar capacidad de refugios",
            "description": f"Alerta: Capacidad de refugios ({total_shelter_capacity}) puede ser insuficiente",
            "actions": ["Identificar espacios adicionales", "Coordinar con instituciones", "Preparar suministros"]
        })
    
    # Monitoreo de tendencias
    trends = analyze_trends(alerts)
    if trends.get('increasing'):
        recommendations.append({
            "type": "preparation",
            "title": "Prepararse para aumento de demanda",
            "description": "Tendencia creciente en número de alertas",
            "actions": ["Revisar planes de contingencia", "Verificar inventario de suministros", "Coordinar con voluntarios"]
        })
    
    return RecommendationResponse(
        recommendations=recommendations,
        priority="MEDIUM",
        validity_period="4h"
    )

def generate_citizen_recommendations(alerts: List[Dict], shelters: List[Dict], location: Dict) -> RecommendationResponse:
    """Recomendaciones para ciudadanos"""
    nearby_alerts = get_nearby_alerts(alerts, location, max_distance=0.01)
    nearby_shelters = get_nearby_shelters(shelters, location, max_distance=0.02)
    
    recommendations = []
    
    if nearby_alerts:
        high_severity_nearby = any(a.get('severity', 1) >= 3 for a in nearby_alerts)
        
        if high_severity_nearby:
            recommendations.append({
                "type": "safety",
                "title": "¡Alerta de seguridad!",
                "description": "Alertas de alta severidad en tu área. Tome precauciones.",
                "actions": ["Manténgase informado", "Siga instrucciones oficiales", "Prepare kit de emergencia"]
            })
        
        recommendations.append({
            "type": "information",
            "title": "Alertas en tu área",
            "description": f"{len(nearby_alerts)} alertas reportadas cerca de tu ubicación",
            "actions": ["Monitorear actualizaciones", "Identificar rutas seguras", "Conocer refugios cercanos"]
        })
    
    if nearby_shelters:
        recommendations.append({
            "type": "preparation",
            "title": "Refugios disponibles",
            "description": f"{len(nearby_shelters)} refugios identificados en tu área",
            "actions": ["Conocer ubicaciones", "Guardar contactos", "Preparar ruta de evacuación"]
        })
    
    if not recommendations:
        recommendations.append({
            "type": "general",
            "title": "Situación normal",
            "description": "No hay alertas críticas en tu área inmediata",
            "actions": ["Mantener preparación básica", "Conocer números de emergencia", "Seguir fuentes oficiales"]
        })
    
    return RecommendationResponse(
        recommendations=recommendations,
        priority="LOW",
        validity_period="6h"
    )

def generate_general_recommendations(alerts: List[Dict]) -> RecommendationResponse:
    """Recomendaciones generales"""
    return RecommendationResponse(
        recommendations=[{
            "type": "general",
            "title": "Monitoreo del sistema",
            "description": f"Sistema activo con {len(alerts)} alertas registradas",
            "actions": ["Revisar dashboard regularmente", "Reportar situaciones anómalas", "Mantener actualizado el perfil"]
        }],
        priority="LOW",
        validity_period="12h"
    )

# Funciones auxiliares
def get_nearby_alerts(alerts: List[Dict], location: Dict, max_distance: float = 0.01) -> List[Dict]:
    if not location:
        return []
    
    lat, lon = location.get('lat', 0), location.get('lon', 0)
    return [
        alert for alert in alerts
        if ((alert.get('lat', 0) - lat)**2 + (alert.get('lon', 0) - lon)**2)**0.5 <= max_distance
    ]

def get_nearby_shelters(shelters: List[Dict], location: Dict, max_distance: float = 0.02) -> List[Dict]:
    if not location:
        return []
    
    lat, lon = location.get('lat', 0), location.get('lon', 0)
    return [
        shelter for shelter in shelters
        if ((shelter.get('lat', 0) - lat)**2 + (shelter.get('lon', 0) - lon)**2)**0.5 <= max_distance
    ]

def analyze_trends(alerts_data: List[Dict]) -> Dict[str, Any]:
    # Implementación simplificada
    if len(alerts_data) < 2:
        return {"trend": "stable"}
    
    recent = [a for a in alerts_data 
              if datetime.fromisoformat(a['created_at'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(hours=24)]
    
    return {
        "trend": "increasing" if len(recent) > len(alerts_data) * 0.3 else "stable",
        "increasing": len(recent) > len(alerts_data) * 0.3
    }

def analyze_location_clusters(alerts_data: List[Dict]) -> List[Dict]:
    # Implementación simplificada
    clusters = []
    for alert in alerts_data:
        lat, lon = alert.get('lat', 0), alert.get('lon', 0)
        
        found = False
        for cluster in clusters:
            c_lat, c_lon = cluster['center']
            if ((lat - c_lat)**2 + (lon - c_lon)**2)**0.5 < 0.01:
                cluster['alerts'].append(alert)
                found = True
                break
        
        if not found:
            clusters.append({
                'center': (lat, lon),
                'alerts': [alert]
            })
    
    return [c for c in clusters if len(c['alerts']) > 1]