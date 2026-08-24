import json # import json library to serilize dict patloads into string format for SQL storage
from os import getenv # to retreive environment variables safely
from dotenv import load_dotenv # load environemnt vriables from local .env file
from fastapi import FastAPI, Request , status, Depends, HTTPException  # request/response management
from fastapi.responses import JSONResponse # format HTTP responses with status codes
from fastapi.exceptions import RequestValidationError # catch failing pydantic validations
from mssql_python import connect

from schemas_rules import TruckTelemetry, DeadLetterRecord


load_dotenv()
app = FastAPI(title ="AHS telemetry Ingestion Service")

# Helper function to open database connection
def get_db():
    conn_str = getenv("AZURE_SQL_CONNECTIONSTRING")
    
    if not conn_str:
        raise HTTPException(
            status_code=500, 
            detail="AZURE_SQL_CONNECTIONSTRING environment variable is missing."
        )
    
    try:
        conn = connect(conn_str)
        yield conn
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database Connection Error: {str(e)}"
        )
    finally:
        if 'conn' in locals():
            conn.close()
     


# global exception handler for all pydantic validation failure
# Tells FastAPI: "Whenever schemas_rules.py throws an error, run this function automatically"
@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    # grab raw incoming dict directly from exception 
    raw_body = exc.body if isinstance(exc.body, dict) else {}

    # extract first error detial from Pydantic's error payload 
    err = exc.errors()[0]
    # format the json key path of failing field
    failing_field= "->".join(str(loc) for loc in err ["loc"])

    # 3. Instantiate DLQ object using imported DeadLetterRecord model so clean and organise the data saved in DataLetterRecord for bad entry
    dlq = DeadLetterRecord(
        truck_id=str(raw_body.get("truck_id", "UNKNOWN")),
        raw_payload=raw_body,
        rejected_field=failing_field,
        rejected_value=str(err.get("input", "MISSING")),  # Invalid value straight from Pydantic
        error_message=err["msg"],
    )

    # transfer the organised and processed payload into azure SQL DLQ audit table for bad entry 
    try:
        #open database connection context manager
        conn =next(get_db())
        try:
            cursor = conn.cursor()
            #execute SQL command to log quarantined data
            cursor.execute(
                """
                INSERT INTO dbo.telemetry_dead_letter_queue
                (dlq_id, truck_id, raw_payload, rejected_field, rejected_value, error_message, failed_at)
                VALUES (?,?,?,?,?,?,?)"""
                ,
                (
                    dlq.dlq_id,
                    dlq.truck_id,
                    json.dumps(dlq.raw_payload),
                    dlq.rejected_field,
                    dlq.rejected_value,
                    dlq.error_message,
                    str(dlq.failed_at)
                ),
            )

            # Commit transactions to database
            conn.commit()
        finally:
            conn.close()
    # catch DB errors to prevent crashes if login fails
    except Exception as db_err:
        print(f"DLQ Persistence failure: {db_err}")

    # return HTTP422 alert response containing unique tracking LDQ references 
    return JSONResponse(
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT,
        content = {"status":"QUARANTINED", "reason": dlq.error_message, "dlq_id": dlq.dlq_id },

    )



# 1. HEALTH CHECK and verify if server is alive
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 2. GET ALL clean staging EVENTS (Read from Azure SQL)
@app.get("/events")
def get_events(conn = Depends(get_db)):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.stg_ahs_events ORDER BY timestamp DESC")
        cols = [col[0] for col in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]


# 3. CREATE AN EVENT (Write to Azure SQL)
@app.post("/events", status_code = status.HTTP_201_CREATED)
def create_event(telemetry: TruckTelemetry, conn = Depends(get_db)):
    # Execution reaches this block only if payload passes all rules in schema_rules
    cursor = conn.cursor()
        # Insert validated clean record into primary tagin table
    cursor.execute(
        """
        INSERT INTO dbo.stg_ahs_events 
        (truck_id, vendor_id, timestamp, mine_zone, network_latency_ms, engine_temp_c,hydraulic_pressure_bar,tyre_temp_c,speed_kmh,fault_code)
        VALUES (?, ?, ?, ?, ?, ?,?,?,?,?)
        """,
        (
            telemetry.truck_id,
            telemetry.vendor_id,
            telemetry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            telemetry.mine_zone,
            telemetry.network_latency_ms,
            telemetry.engine_temp_c,
            telemetry.hydraulic_pressure_bar,
            telemetry.tyre_temp_c,
            telemetry.speed_kmh,
            telemetry.fault_code
        ),
    )
    conn.commit()
# return confirmation back to edge gateway
    return {"status":"ACCEPTED", "data":telemetry}



