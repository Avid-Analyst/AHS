from unittest.mock import patch, MagicMock
from app import app, get_db, handle_validation_error, health_check, get_events, create_event 
import pytest
import os
from fastapi.exceptions import RequestValidationError
from schemas_rules import TruckTelemetry
from fastapi.testclient import TestClient
from datetime import datetime , timezone
import sqlite3



db_sample =TruckTelemetry(truck_id ="CAT-1",
        vendor_id = "Caterpillar",
        timestamp= datetime(2025, 8, 22, 10, 15, tzinfo=timezone.utc),
        mine_zone= "North_pit",
        network_latency_ms=45,
        engine_temp_c=92.5,
        hydraulic_pressure_bar=210.0,
        tyre_temp_c=65.0,
        speed_kmh=28.4,
        fault_code= None
    )

db_sample_ =TruckTelemetry(truck_id ="CAT-2",
        vendor_id = "Caterpillar",
        timestamp= datetime(2025, 8, 22, 10, 16, tzinfo=timezone.utc),
        mine_zone= "South_pit",
        network_latency_ms=25,
        engine_temp_c=92.0,
        hydraulic_pressure_bar=210.0,
        tyre_temp_c=65.0,
        speed_kmh=28.4,
        fault_code= None
    )

def test_get_db():
    with patch ("app.connect") as mock_connect:
        next(get_db())
        mock_connect.assert_called_once()
        
        called_argument = mock_connect.call_args[0][0]
        assert called_argument == os.environ.get("AZURE_SQL_CONNECTIONSTRING")


def test_handle_validation_error():

    fake_raw_body ={"truck_id":"Test_truck","speed_kmh":"Test_speed"}
    # use fakeFASTAPI requestvalidationerror and exc agrument witth fake error list 
    fake_errors = [{"loc":("body","speed_kmh"), "msg":"value is not a valid integer", "input":"test_speed"}]

    # use MagicMock to fake exc object
    mock_exc = MagicMock(spec=RequestValidationError)
    mock_exc.body =fake_raw_body
    mock_exc.errors.return_value = fake_errors

    #blank request object as handler expect it as 1st agrument
    mock_request = MagicMock()

    # fake connect as before to get around sql connect availability
    with patch("app.get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = iter([mock_conn])

        # finally calling actual function with our fake objects
        response = handle_validation_error(mock_request, mock_exc)

        assert response.status_code == 422
        assert "QUARANTINED" in response.body.decode()



'''def test_create_event():
    
    with patch("app.get_db") as _:
        response = app.create_event(db_sample)

    assert response["status"] == "ACCEPTED"
    assert response["data"].vendor_id =="Caterpillar"
    '''


@pytest.fixture
def test_client():
    return TestClient(app)

def test_health_check(test_client):
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status":"healthy"}

def test_get_events(test_client):
    dict1 = db_sample.model_dump(mode="json")
    dict2 = db_sample_.model_dump(mode="json")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.description = tuple ((col,) for col in dict1.keys())
    mock_cursor.fetchall.return_value = [tuple(dict1.values()), tuple(dict2.values())]
    mock_conn.cursor.return_value = mock_cursor

    def override_get_db():
        yield mock_conn

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = test_client.get("/events")
        assert response.status_code ==200
        expected_output = [dict1, dict2]
        print(expected_output)
        

        assert response.json() == expected_output
    finally:
        app.dependency_overrides.clear()

    
def test_create_event(test_client):
    conn = sqlite3.connect(":memory:", check_same_thread= False)
    cursor = conn.cursor()

    cursor.execute("ATTACH DATABASE ':memory:' AS dbo;")
    cursor.execute("""
        CREATE TABLE dbo.stg_ahs_events (
            truck_id TEXT, 
            vendor_id TEXT, 
            timestamp TEXT, 
            mine_zone TEXT, 
            network_latency_ms INT, 
            engine_temp_c REAL, 
            hydraulic_pressure_bar REAL, 
            tyre_temp_c REAL, 
            speed_kmh REAL, 
            fault_code TEXT
        )
    """
    )
    insert_sql = "INSERT INTO dbo.stg_ahs_events VALUES (?,?,?,?,?,?,?,?,?,?)"
    cursor.execute (insert_sql, tuple(db_sample.model_dump(mode="json").values()))
    cursor.execute (insert_sql, tuple(db_sample_.model_dump(mode="json").values()))
    conn.commit()

    ## over ride get_db context manager to supply this in memeory database
    def override_get_db():
        yield conn

    app.dependency_overrides[get_db] = override_get_db

    try:
        # send post request with db_sample payload
        incoming_payload = db_sample.model_dump(mode="json")
        response = test_client.post("/events", json=incoming_payload)

        # time to shine
        assert response.status_code == 201
        assert response.json()["status"] == "ACCEPTED"
        assert response.json()["data"]["truck_id"]  == "CAT-1"

        #checking if appended actually grew the database
        cursor.execute("SELECT truck_id, speed_kmh FROM stg_ahs_events")
        all_rows = cursor.fetchall()

        assert len(all_rows) == 3
        assert all_rows[2][0] == "CAT-1"
        assert all_rows[2][1] == 28.4

    finally:
        app.dependency_overrides.clear()
        conn.close()

    



