import os
import logging
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# Cargar variables de entorno PRIMERO
load_dotenv()

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alerts.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

app = FastAPI(title="Backend - Alerta Desastres")

# Configurar CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELOS =====
class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = ""
    lat: float
    lon: float
    severity: int = 1
    alert_type: str = "general"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Zone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    geojson: str
    zone_type: str = "risk"

class Shelter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    lat: float
    lon: float
    capacity: Optional[int] = None
    shelter_type: str = "refuge"

class PushSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    p256dh: str
    auth: str

# ===== MODELOS PYDANTIC =====
class AlertCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    lat: float
    lon: float
    severity: Optional[int] = 1
    alert_type: Optional[str] = "general"

class SubscriptionCreate(BaseModel):
    endpoint: str
    keys: dict

# ===== SERVICIOS =====
from .twilio_service import twilio_service

# ===== FUNCIONES AUXILIARES =====
def create_tables_safe():
    """Crear tablas manejando posibles errores"""
    try:
        SQLModel.metadata.create_all(engine)
        logging.info("✅ Tablas creadas exitosamente")
    except Exception as e:
        logging.error(f"❌ Error creando tablas: {e}")
        if "no such column" in str(e):
            logging.info("🔄 Recreando base de datos...")
            recreate_database()
        else:
            raise e

def recreate_database():
    """Recrear la base de datos desde cero"""
    try:
        if os.path.exists("alerts.db"):
            os.remove("alerts.db")
            logging.info("🗑️ Base de datos anterior eliminada")
        
        SQLModel.metadata.create_all(engine)
        logging.info("✅ Nueva base de datos creada")
        seed_initial_data()
        
    except Exception as e:
        logging.error(f"❌ Error recreando base de datos: {e}")
        raise e

def seed_initial_data():
    """Datos iniciales para prueba"""
    with Session(engine) as session:
        # Zonas
        if not session.exec(select(Zone)).first():
            zones = [
                Zone(
                    name="Zona de Inundación - Río Centro", 
                    geojson='{"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-90.53,14.62],[-90.52,14.62],[-90.52,14.63],[-90.53,14.63],[-90.53,14.62]]]}}]}',
                    zone_type="risk"
                ),
                Zone(
                    name="Área Segura - Parque Central",
                    geojson='{"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-90.52,14.63],[-90.51,14.63],[-90.51,14.64],[-90.52,14.64],[-90.52,14.63]]]}}]}',
                    zone_type="safe"
                )
            ]
            for zone in zones:
                session.add(zone)
        
        # Refugios
        if not session.exec(select(Shelter)).first():
            shelters = [
                Shelter(name="Escuela Central - Refugio Principal", lat=14.625, lon=-90.525, capacity=200, shelter_type="refuge"),
                Shelter(name="Hospital General", lat=14.635, lon=-90.515, capacity=150, shelter_type="hospital"),
                Shelter(name="Estadio Municipal", lat=14.615, lon=-90.535, capacity=500, shelter_type="meeting_point"),
            ]
            for shelter in shelters:
                session.add(shelter)
        
        session.commit()
        logging.info("📊 Datos iniciales cargados")

def notify_all(alert: Alert):
    """Enviar notificaciones a todos los servicios"""
    try:
        from .notifications import notify_all_services
        
        alert_data = {
            "id": alert.id,
            "title": alert.title,
            "description": alert.description,
            "lat": alert.lat,
            "lon": alert.lon,
            "severity": alert.severity,
            "alert_type": alert.alert_type,
            "created_at": alert.created_at.isoformat()
        }
        
        with Session(engine) as session:
            push_subscriptions = session.exec(select(PushSubscription)).all()
        
        notify_all_services(alert_data, push_subscriptions)
                
    except Exception as e:
        logging.error(f"❌ Error en notify_all: {e}")

# ===== EVENTOS DE APLICACIÓN =====
@app.on_event("startup")
def on_startup():
    create_tables_safe()
    logging.info("✅ Backend iniciado correctamente")

# ===== ENDPOINTS =====
@app.get("/")
def read_root():
    return {"message": "🚀 Backend de Alertas funcionando"}

@app.get("/health")
def health_check():
    """Verificar estado del sistema"""
    with Session(engine) as session:
        alert_count = len(session.exec(select(Alert)).all())
        zone_count = len(session.exec(select(Zone)).all())
        shelter_count = len(session.exec(select(Shelter)).all())
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "alerts": alert_count,
            "zones": zone_count,
            "shelters": shelter_count
        },
        "version": "2.0.0"
    }

@app.get("/twilio-status")
def get_twilio_status():
    """Verificar estado de Twilio"""
    status = twilio_service.get_configuration_status()
    return {
        "twilio_status": status,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/alerts", response_model=List[Alert])
def list_alerts(limit: int = 100):
    """Obtener todas las alertas"""
    try:
        with Session(engine) as session:
            alerts = session.exec(
                select(Alert).order_by(Alert.created_at.desc()).limit(limit)
            ).all()
            logging.info(f"📊 {len(alerts)} alertas encontradas")
            return alerts
    except Exception as e:
        logging.error(f"❌ Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/alerts", response_model=Alert, status_code=201)
def create_alert(alert_data: AlertCreate):
    """Crear una nueva alerta"""
    try:
        logging.info(f"📨 Recibiendo alerta: {alert_data}")
        
        if not alert_data.title or not alert_data.lat or not alert_data.lon:
            raise HTTPException(status_code=400, detail="Faltan campos requeridos")
        
        alert = Alert(
            title=alert_data.title,
            description=alert_data.description,
            lat=alert_data.lat,
            lon=alert_data.lon,
            severity=alert_data.severity,
            alert_type=alert_data.alert_type
        )
        
        with Session(engine) as session:
            session.add(alert)
            session.commit()
            session.refresh(alert)
        
        logging.info(f"✅ Alerta creada: {alert.id} - {alert.title}")
        
        try:
            notify_all(alert)
        except Exception as e:
            logging.warning(f"⚠️ Error en notificaciones: {e}")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error creando alerta: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/zones", response_model=List[Zone])
def get_zones():
    """Obtener todas las zonas"""
    with Session(engine) as session:
        return session.exec(select(Zone)).all()

@app.get("/shelters", response_model=List[Shelter])
def get_shelters():
    """Obtener todos los refugios"""
    with Session(engine) as session:
        return session.exec(select(Shelter)).all()

@app.post("/subscribe", status_code=201)
def subscribe(subscription: SubscriptionCreate):
    """Guardar suscripción para notificaciones push"""
    try:
        with Session(engine) as session:
            existing = session.exec(
                select(PushSubscription).where(PushSubscription.endpoint == subscription.endpoint)
            ).first()
            
            if not existing:
                sub = PushSubscription(
                    endpoint=subscription.endpoint,
                    p256dh=subscription.keys.get("p256dh"),
                    auth=subscription.keys.get("auth")
                )
                session.add(sub)
                session.commit()
                session.refresh(sub)
                return {"message": "Suscripción guardada", "id": sub.id}
            else:
                return {"message": "Suscripción ya existe", "id": existing.id}
    except Exception as e:
        logging.error(f"Error en suscripción: {e}")
        raise HTTPException(status_code=500, detail="Error guardando suscripción")

@app.post("/dev/reset-database")
def reset_database():
    """Resetear base de datos (SOLO DESARROLLO)"""
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Solo disponible en desarrollo")
    
    recreate_database()
    return {"message": "Base de datos reseteada"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")