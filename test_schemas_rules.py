from schemas_rules import *
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError


error_list =[]
# checking invalids- out of bounds
invalid_matrix = {

    "valid_data" : [{

    "truck_id": "CAT-1",
    "vendor_id": "Caterpillar",
        #"timestamp":"2026-08-22T10:15:00Z",
    "timestamp":datetime.now(timezone.utc),
    "mine_zone": "North_pit",
    "network_latency_ms":45,
    "engine_temp_c":92.5,
    "hydraulic_pressure_bar":210.0,
    "tyre_temp_c": 65.0,
    "speed_kmh": 28.4,
    "fault_code": None
    }],
    
    "truck_id": [""],
    "vendor_id": [""],
    "timestamp": ["abc"],
    "mine_zone": [""],
    "network_latency_ms": [-45, "nbn"],
    "engine_temp_c": [250.0, "Warning:hot",-999],              
    "hydraulic_pressure_bar": ["5 bar",910.0, -220],
    "tyre_temp_c": ["what", -500, 200],
    "speed_kmh": ["too-fast", -5, -5.5, 100], 
    }


@pytest.mark.parametrize(
    "field_name, test_value",
    [
        (field,val)
        for field, values in invalid_matrix.items()
        for val in values
    ]
)


def test_truck_telemetry_all_values( field_name, test_value):
    base_data = invalid_matrix["valid_data"][0].copy() # default value once inalid gets started
    if field_name == "valid_data":
        telemetry_obj = TruckTelemetry(**test_value)
        assert telemetry_obj.truck_id == "CAT-1"
        assert telemetry_obj.vendor_id == "Caterpillar"
        assert isinstance(telemetry_obj.timestamp, datetime) #.now(timezone.utc))
        assert telemetry_obj.engine_temp_c == 92.5

    else:
        base_data[field_name] = test_value
    
        with pytest.raises(ValidationError) as exc_info:
            TruckTelemetry(**base_data)
    
        errors = exc_info.value.errors()
        actual_failed_fields = {err["loc"][0] for err in errors}
        assert actual_failed_fields == {field_name}

        for err in errors:
            error_list.append(
                {
                    "field": err["loc"][0], "msg": err["msg"], "input":err["input"],

                }   
            )



def test_print_error():
    print("\n--- INVALID PAYLOAD ERRORS ---")
    print(f"\n Total Errors Found: {len(error_list)}")
    for item in error_list:
            print(f" \n\n for {item['field']}, {item['msg']}, but was given as : {item['input']} ")

    

# test tdl class
def test_dead_letter_record_default_generation():
    dlq_record = DeadLetterRecord(
        raw_payload= {"truck_id":"CAT-01","":""},
        rejected_field = "engine_temp_c",
        rejected_value="INVALID",
        error_message="INput must be valid number"
        )
    assert dlq_record.truck_id =="UNKNOWN"
    assert len(dlq_record.dlq_id) == 36
    assert isinstance(dlq_record.failed_at, datetime)
