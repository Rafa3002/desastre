import os
import logging
import json
from dotenv import load_dotenv
from .twilio_service import twilio_service

load_dotenv()

# Configuración push
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_SUB = os.getenv("VAPID_SUB", "mailto:admin@example.com")

def send_push_notification(subscription_info: dict, message: str):
    """Envía notificación push"""
    if not VAPID_PRIVATE_KEY:
        return
    
    try:
        from pywebpush import webpush
        
        notification_data = {
            "title": "🚨 Alerta de Desastre",
            "body": message,
            "icon": "/favicon.ico"
        }
        
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_SUB}
        )
        
    except Exception as e:
        logging.error(f"❌ Error en push: {e}")

def notify_all_services(alert_data: dict, push_subscriptions: list = None):
    """Envía notificaciones a todos los servicios"""
    logging.info("🔔 Enviando notificaciones...")
    
    # 1. Enviar SMS
    sms_success = twilio_service.send_alert_sms(alert_data)
    
    # 2. Enviar Push
    if push_subscriptions:
        message = f"🚨 {alert_data.get('title', 'Nueva alerta')}"
        for subscription in push_subscriptions:
            send_push_notification({
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth
                }
            }, message)
    
    logging.info(f"✅ Notificaciones completadas - SMS: {'✅' if sms_success else '❌'}")