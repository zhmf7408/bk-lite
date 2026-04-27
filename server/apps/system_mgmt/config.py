from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "check_password_expiry_and_notify": {
        "task": "apps.system_mgmt.tasks.check_password_expiry_and_notify",
        "schedule": crontab(hour=0, minute=0),
    },
}
