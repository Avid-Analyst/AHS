from os import getenv
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from mssql_python import connect

load_dotenv()

connection_string = getenv("AZURE_SQL_CONNECTIONSTRING")

app = FastAPI()


class AHSEvent(BaseModel):
    event_id: int
    truck_id: str
    location_id: str | None = None
    event_type: str
    event_timestamp: datetime
    payload_tonnes: float | None = None


@app.get("/")

def root():
    return "AHS Event API"

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/events")
def get_events():
    rows = []

    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                stg_id,
                event_id,
                truck_id,
                location_id,
                event_type,
                event_timestamp,
                payload_tonnes,
                created_at
            FROM dbo.stg_ahs_events
            ORDER BY stg_id
        """)

        for row in cursor.fetchall():
            rows.append({
                "stg_id": row.stg_id,
                "event_id": row.event_id,
                "truck_id": row.truck_id,
                "location_id": row.location_id,
                "event_type": row.event_type,
                "event_timestamp": row.event_timestamp,
                "payload_tonnes": row.payload_tonnes,
                "created_at": row.created_at
            })

    return rows


@app.post("/events")
def create_event(item: AHSEvent):

    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dbo.stg_ahs_events
            (
                event_id,
                truck_id,
                location_id,
                event_type,
                event_timestamp,
                payload_tonnes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item.event_id,
            item.truck_id,
            item.location_id,
            item.event_type,
            item.event_timestamp,
            item.payload_tonnes
        ))

        conn.commit()

    return item


def get_conn():
    """Connect using mssql-python with Microsoft Entra authentication."""
    conn = connect(connection_string)
    conn.setautocommit(True)
    return conn