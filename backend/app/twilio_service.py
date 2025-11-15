import os
import logging
from dotenv import load_dotenv

load_dotenv()

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.alert_numbers = [num.strip() for num in os.getenv("ALERT_PHONE_NUMBERS", "").split(",") if num.strip()]
        
        self.client = None
        self.is_configured = False
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializar el cliente Twilio"""
        try:
            if not all([self.account_sid, self.auth_token, self.phone_number]):
                logging.warning("⚠️ Twilio no está completamente configurado")
                return
            
            from twilio.rest import Client
            self.client = Client(self.account_sid, self.auth_token)
            self.is_configured = True
            logging.info("✅ Twilio configurado correctamente")
            
        except ImportError:
            logging.error("❌ Twilio no está instalado. Ejecuta: pip install twilio")
        except Exception as e:
            logging.error(f"❌ Error inicializando Twilio: {e}")
    
    def send_alert_sms(self, alert_data):
        """Enviar SMS de alerta"""
        if not self.is_configured:
            logging.warning("⚠️ Twilio no configurado - Saltando SMS")
            return False
        
        if not self.alert_numbers:
            logging.warning("⚠️ No hay números configurados para alertas SMS")
            return False
        
        success_count = 0
        
        for phone_number in self.alert_numbers:
            try:
                message_body = self._format_alert_message(alert_data)
                
                message = self.client.messages.create(
                    body=message_body,
                    from_=self.phone_number,
                    to=phone_number
                )
                
                logging.info(f"✅ SMS enviado a {phone_number}")
                success_count += 1
                
            except Exception as e:
                logging.error(f"❌ Error enviando SMS a {phone_number}: {e}")
        
        logging.info(f"✅ SMS enviados: {success_count}/{len(self.alert_numbers)} exitosos")
        return success_count > 0
    
    def _format_alert_message(self, alert_data):
        """Formatear el mensaje de alerta para SMS"""
        type_emojis = {
            'inundacion': '🌊',
            'terremoto': '🏚️', 
            'incendio': '🔥',
            'deslizamiento': '⛰️',
            'general': '⚠️'
        }
        
        severity_levels = {
            1: ('BAJA', '🟢'),
            2: ('MEDIA', '🟡'),
            3: ('ALTA', '🔴'), 
            4: ('CRÍTICA', '🚨')
        }
        
        alert_type = alert_data.get('alert_type', 'general')
        severity = alert_data.get('severity', 1)
        
        type_emoji = type_emojis.get(alert_type, '⚠️')
        severity_text, severity_emoji = severity_levels.get(severity, ('DESCONOCIDA', '⚪'))
        
        message = f"""
{type_emoji} ALERTA DE {severity_text} {severity_emoji}

{alert_data.get('title', 'Alerta de emergencia')}

📍 Ubicación: {alert_data.get('lat', 0):.4f}, {alert_data.get('lon', 0):.4f}
📋 Nivel: {severity_text}

{alert_data.get('description', 'Situación de emergencia reportada.')}

🚨 Tome precauciones.
Sistema de Alertas
        """.strip()
        
        if len(message) > 1600:
            message = message[:1597] + "..."
            
        return message
    
    def get_configuration_status(self):
        """Obtener estado de la configuración de Twilio"""
        return {
            'configured': self.is_configured,
            'account_sid_set': bool(self.account_sid),
            'auth_token_set': bool(self.auth_token),
            'phone_number_set': bool(self.phone_number),
            'alert_numbers_count': len(self.alert_numbers),
            'alert_numbers': self.alert_numbers
        }

# Instancia global
twilio_service = TwilioService()