
self.addEventListener('push', function(event) {
  let data = {};
  if (event.data) {
    data = event.data.json();
  }
  const title = data.title || "Alerta Desastre";
  const options = {
    body: data.body || "Nueva alerta",
    icon: '/icons/icon-192x192.png',
    data: data.url || '/'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data;
  event.waitUntil(clients.openWindow(url));
});

self.addEventListener("push", e => {
  const data = e.data ? e.data.text() : "Alerta de desastre";
  self.registration.showNotification("Alerta", { body: data });
});
