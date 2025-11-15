import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const publicVapidKey = process.env.REACT_APP_VAPID_PUBLIC_KEY;

// Función para convertir base64 a Uint8Array
function urlBase64ToUint8Array(base64String) {
  if (!base64String) {
    console.error('VAPID public key no configurada');
    return null;
  }
  
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Registrar Service Worker y suscripción
async function registerServiceWorker() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications no soportadas en este navegador');
    return;
  }

  if (!publicVapidKey) {
    console.warn('VAPID public key no configurada');
    return;
  }

  try {
    console.log('Registrando Service Worker...');
    
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/'
    });
    
    console.log('Service Worker registrado correctamente');

    // Esperar a que el Service Worker esté activo
    await registration.active;

    // Pedir permiso para notificaciones
    const permission = await Notification.requestPermission();
    
    if (permission !== 'granted') {
      console.warn('Permiso de notificaciones no concedido');
      return;
    }

    console.log('Permiso de notificaciones concedido');

    // Suscribirse a push notifications
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
    });

    console.log('Suscripción push creada:', subscription);

    // Enviar suscripción al backend
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscription),
    });

    if (response.ok) {
      console.log('Suscripción enviada al backend correctamente');
    } else {
      console.error('Error enviando suscripción al backend:', await response.text());
    }

  } catch (error) {
    console.error('Error en registro de Service Worker:', error);
  }
}

// Iniciar la aplicación
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

// Registrar Service Worker después de renderizar la app
setTimeout(registerServiceWorker, 1000);