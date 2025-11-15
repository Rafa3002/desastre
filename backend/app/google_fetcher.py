import os
import requests
from sqlmodel import Session, select
from .models import Alert

GOOGLE_URL = os.getenv("GOOGLE_ALERTS_API")

def fetch_google_alerts(session: Session):
    r = requests.get(GOOGLE_URL)
    data = r.json()

    for alert in data.get("alerts", []):
        title = alert.get("title")
        desc = alert.get("description")
        severity = alert.get("severity", 2)
        lat = alert.get("coordinates", {}).get("lat", 0)
        lon = alert.get("coordinates", {}).get("lng", 0)

        exists = session.exec(
            select(Alert).where(Alert.title == title)
        ).first()

        if not exists:
            new = Alert(
                title=title,
                description=desc,
                severity=severity,
                lat=lat,
                lon=lon,
                source="GOOGLE"
            )
            session.add(new)
            session.commit()
            session.refresh(new)
