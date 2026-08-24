from datetime import datetime, timezone
from typing import Optional, Annotated
import uuid
from pydantic import BaseModel, Field, field_validator, StringConstraints

#valid data needs
StrippedString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
class TruckTelemetry(BaseModel):
    # 1. Identity
    truck_id : StrippedString = Field(..., description="Unique ID of truck")
    vendor_id : StrippedString = Field(..., description="E.g., CAT or KOMATSU or another")


    # 2. Context
    timestamp: datetime =Field(..., description = "Event time on truck" )
    mine_zone: StrippedString = Field(..., description= "current pit location")

    # 3. Network Health
    network_latency_ms : int = Field (description= "ping time in millisecond", ge=0)

    # 4. Physcial health 
    engine_temp_c : float = Field( description = "Engine temp in Celsius",ge=-20.0, le=150.0) 
    hydraulic_pressure_bar : float = Field (description = "Hydraulic pressure",ge=0.0,le=350.0)
    tyre_temp_c : float = Field(..., description = "tyre surface temp in Celsius", ge=-40.0,le=120.0)
    speed_kmh : float = Field(..., description= "vehicle speed in km/h",ge=0.0,le=80.0) 

    # 5. Diagnostics
    fault_code : Optional[str] =Field(default = None, description = "Error code if present")


    """# Domain validation rules-- FUTURE USE WHEN DATA GET COMPLICATED
    @field_validator("network_latency_ms")
    @classmethod
    def validate_latency(cls, value: int) -> int:
        #latency can not be negative
        if value <0 :
            raise ValueError(f"Network latency ({value} ms) cannot be negative. ")
        return value

    @field_validator("engine_temp_c")
    @classmethod
    def validate_engine_temp(cls, value:float) ->float:
        #Operating range: -20Cto 150C
        if not (-20.0 <= value <= 150.0 ):
            raise ValueError(f"engine temp is ({value} c) out of safe bound (-20C to 150C)")
        return value

    @field_validator("hydraulic_pressure_bar")
    @classmethod
    def validate_hydraulic_pressure(cls, value: float) -> float:
        # pressure can not be negative or exceed maximum system relief value 
        if not (0.0 <= value <= 350.0):
            raise ValueError(f"Hydraulic pressure ({value} Bar) is out of safe bounds (0.0 to 350.0 Bar)")
        return value
    
    @field_validator("tyre_temp_c")
    @classmethod
    def validate_tyre_temp(cls, value: float) -> float:
        #tyre thermal limits -40C to 120C
        if not (-40.0 <= value <= 120.0):
            raise ValueError(f"Tyre temp ({value} C) out of safe bounds (-40C to 120C")
        return value
        
    @field_validator("speed_kmh")
    @classmethod
    def validate_speed(cls, value: float) -> float:
        # Ultra haul truck cannot travel negative speeds or exceeding physical mac 80mk/h
        if not (0.0 <= value <= 80.0):
            raise ValueError (f"vehicle speed ({value} km/h) out of physical operating limits (0 to 80 km/h)")
        return value
    """


# Data collected for bad or invalid entries
class DeadLetterRecord(BaseModel):
    """
    Schema for logging rejedcted payloads into our audit table and notifying the ROC.
    """
    dlq_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    truck_id: Optional[str] = "UNKNOWN"
    raw_payload: dict
    rejected_field: str
    rejected_value: str
    error_message: str
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
