registerServiceWorker(
    "/static/service_worker.js",
    "{{config['VAPID_PUBLIC_KEY']}}",
    "/api/push-subscriptions"
);