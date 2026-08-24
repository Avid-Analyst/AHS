DROP TABLE IF EXISTS dbo.stg_ahs_events;
DROP TABLE IF EXISTS dbo.telemetry_dead_letter_queue;

-- 1. Clean, validated Telemetry Staging
CREATE TABLE dbo.stg_ahs_events (
    event_id INT IDENTITY (1,1) PRIMARY KEY,
    truck_id VARCHAR(50) NOT NULL,
    vendor_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    mine_zone VARCHAR (50) NOT NULL,
    network_latency_ms INT NOT NULL,
    engine_temp_c DECIMAL(5,2) NOT NULL,
    hydraulic_pressure_bar DECIMAL(5,2) NOT NULL,
    tyre_temp_c DECIMAL (5,2) NOT NULL,
    speed_kmh DECIMAL (5,2) NOT NULL,
    fault_code VARCHAR(50) NULL,
    created_at DATETIME DEFAULT GETDATE()
);


--table 2: Dead Letter Queue and anomally audit queue

CREATE TABLE dbo.telemetry_dead_letter_queue (
    dlq_id VARCHAR(100) PRIMARY KEY,
    truck_id VARCHAR (50) NULL,
    raw_payload NVARCHAR(MAX) NOT NULL,
    rejected_field VARCHAR (100) NOT NULL,
    rejected_value VARCHAR(255) NULL,
    error_message NVARCHAR(MAX) NOT NULL,
    failed_at DATETIME DEFAULT GETDATE()
    
);