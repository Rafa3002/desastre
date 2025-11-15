from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import httpx

router = APIRouter(prefix="/mcp/decisions", tags=["decision-support"])

class DecisionRequest(BaseModel):
    scenario: str
    available_resources: Dict[str, Any]
    constraints: List[str] = []

class DecisionResponse(BaseModel):
    recommended_actions: List[str]
    priority_order: List[str]
    resource_allocation: Dict[str, Any]
    rationale: str

@router.post("/emergency-response", response_model=DecisionResponse)
async def emergency_response_plan(request: DecisionRequest):
    """Generar plan de respuesta de emergencia basado en escenario"""
    
    # Obtener datos actuales del sistema
    async with httpx.AsyncClient() as client:
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=50")
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
    
    # Filtrar alertas activas de alta severidad
    high_priority_alerts = [
        alert for alert in alerts_data 
        if alert.get('severity', 1) >= 3
    ]
    
    # Generar recomendaciones basadas en el escenario
    if request.scenario.lower() == "inundacion":
        return generate_flood_response(high_priority_alerts, request.available_resources)
    elif request.scenario.lower() == "terremoto":
        return generate_earthquake_response(high_priority_alerts, request.available_resources)
    elif request.scenario.lower() == "incendio":
        return generate_fire_response(high_priority_alerts, request.available_resources)
    else:
        return generate_generic_response(high_priority_alerts, request.available_resources)

def generate_flood_response(alerts: List[Dict], resources: Dict) -> DecisionResponse:
    actions = [
        "Activar protocolos de evacuación en zonas bajas",
        "Desplegar equipos de rescate acuático",
        "Establecer centros de evacuación en áreas elevadas",
        "Monitorear niveles de ríos y quebradas",
        "Coordinar con autoridades de gestión de riesgos"
    ]
    
    resource_allocation = {
        "rescue_teams": min(resources.get('rescue_teams', 0), 3),
        "evacuation_centers": resources.get('shelters', 0),
        "medical_teams": resources.get('medical_teams', 0),
        "communication_units": resources.get('communication_units', 0)
    }
    
    return DecisionResponse(
        recommended_actions=actions,
        priority_order=actions[:3],  # Primeras 3 acciones son prioritarias
        resource_allocation=resource_allocation,
        rationale="Protocolo de inundación activado basado en alertas de alta severidad en zonas vulnerables"
    )

def generate_earthquake_response(alerts: List[Dict], resources: Dict) -> DecisionResponse:
    actions = [
        "Evaluar daños estructurales inmediatamente",
        "Buscar y rescatar personas atrapadas",
        "Establecer puestos médicos de emergencia",
        "Evaluar seguridad de infraestructura crítica",
        "Activar centros de operaciones de emergencia"
    ]
    
    return DecisionResponse(
        recommended_actions=actions,
        priority_order=actions,
        resource_allocation={
            "search_rescue_teams": resources.get('rescue_teams', 0),
            "medical_units": resources.get('medical_teams', 0),
            "engineering_teams": resources.get('engineering_teams', 0)
        },
        rationale="Respuesta sísmica priorizando búsqueda, rescate y evaluación estructural"
    )

def generate_fire_response(alerts: List[Dict], resources: Dict) -> DecisionResponse:
    actions = [
        "Contener avance del fuego mediante cortafuegos",
        "Evacuar poblaciones en dirección opuesta al viento",
        "Coordinar con bomberos y equipos de tierra",
        "Monitorear condiciones climáticas y dirección del viento",
        "Establecer perímetros de seguridad"
    ]
    
    return DecisionResponse(
        recommended_actions=actions,
        priority_order=actions,
        resource_allocation={
            "firefighting_teams": resources.get('fire_teams', 0),
            "air_support": resources.get('aircraft', 0),
            "evacuation_teams": resources.get('evacuation_teams', 0)
        },
        rationale="Estrategia de contención y evacuación para incendios forestales/urbanos"
    )

def generate_generic_response(alerts: List[Dict], resources: Dict) -> DecisionResponse:
    actions = [
        "Evaluar situación y priorizar necesidades",
        "Desplegar equipos de primera respuesta",
        "Establecer comunicación con autoridades locales",
        "Monitorear desarrollo de la situación",
        "Actualizar planes basado en nueva información"
    ]
    
    return DecisionResponse(
        recommended_actions=actions,
        priority_order=actions,
        resource_allocation={
            "first_responders": resources.get('response_teams', 0),
            "communication": resources.get('communication_units', 0),
            "medical": resources.get('medical_teams', 0)
        },
        rationale="Respuesta genérica de emergencia adaptativa a múltiples escenarios"
    )

@router.get("/resource-optimization")
async def optimize_resources():
    """Optimizar asignación de recursos basado en alertas actuales"""
    async with httpx.AsyncClient() as client:
        alerts_response = await client.get(f"{BACKEND_URL}/alerts?limit=100")
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else []
    
    # Analizar distribución geográfica de alertas
    clusters = analyze_location_clusters(alerts_data)
    
    optimization_plan = {}
    
    for i, cluster in enumerate(clusters[:5]):  # Máximo 5 clusters
        cluster_alerts = cluster['alerts']
        high_severity_count = len([a for a in cluster_alerts if a.get('severity', 1) >= 3])
        
        optimization_plan[f"zone_{i+1}"] = {
            "center": cluster['center'],
            "alert_count": len(cluster_alerts),
            "high_severity_alerts": high_severity_count,
            "recommended_resources": calculate_required_resources(cluster_alerts),
            "priority": "HIGH" if high_severity_count > 0 else "MEDIUM"
        }
    
    return {
        "optimization_plan": optimization_plan,
        "total_zones": len(clusters),
        "timestamp": datetime.utcnow().isoformat()
    }

def calculate_required_resources(alerts: List[Dict]) -> Dict[str, int]:
    high_severity = len([a for a in alerts if a.get('severity', 1) >= 3])
    total_alerts = len(alerts)
    
    return {
        "medical_teams": min(high_severity, 3),
        "rescue_teams": min(total_alerts // 5 + 1, 5),
        "communication_units": 1 if total_alerts > 0 else 0,
        "logistics_support": min(total_alerts // 10 + 1, 2)
    }

# Función auxiliar (definida en el archivo anterior)
def analyze_location_clusters(alerts_data: List[Dict]) -> List[Dict]:
    # Reutilizar la función del archivo anterior
    clusters = []
    for alert in alerts_data:
        lat, lon = alert.get('lat', 0), alert.get('lon', 0)
        
        found_cluster = None
        for cluster in clusters:
            cluster_lat, cluster_lon = cluster['center']
            distance = ((lat - cluster_lat)**2 + (lon - cluster_lon)**2)**0.5
            if distance < 0.01:
                found_cluster = cluster
                break
        
        if found_cluster:
            found_cluster['alerts'].append(alert)
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
    
    return [c for c in clusters if len(c['alerts']) > 1]