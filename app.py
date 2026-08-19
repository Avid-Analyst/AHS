from os import getenv
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from mssql_python import connect

load_dotenv()
app = FastAPI()


# 1. THE DATA FORM (What incoming data must look like)
class AHSEvent(BaseModel):
    event_id: int
    truck_id: str
    location_id: str | None = None
    event_type: str
    event_timestamp: datetime
    payload_tonnes: float | None = None


# Helper function to open database connection
def get_db():
    return connect(getenv("AZURE_SQL_CONNECTIONSTRING"))


# 2. HEALTH CHECK
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 3. GET ALL EVENTS (Read from Azure SQL)
@app.get("/events")
def get_events():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.stg_ahs_events ORDER BY stg_id")

        # Automatically map column names to values in 1 line
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


# 4. CREATE AN EVENT (Write to Azure SQL)
@app.post("/events")
def create_event(event: AHSEvent):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.stg_ahs_events 
            (event_id, truck_id, location_id, event_type, event_timestamp, payload_tonnes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.truck_id,
                event.location_id,
                event.event_type,
                str(event.event_timestamp),
                event.payload_tonnes,
            ),
        )
        conn.commit()

    return event