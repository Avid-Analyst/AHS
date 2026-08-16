IF OBJECT_ID ('dbo.stg_ahs_events' , 'U') IS NOT NULL
    DROP TABLE dbo.stg_ahs_events;

CREATE TABLE dbo.stg_ahs_events (
    stg_id INT IDENTITY (1,1) PRIMARY KEY,
    event_id INT NOT NULL,
    truck_id VARCHAR(10) NOT NULL,
    location_id VARCHAR(30) NULL,
    event_type VARCHAR(20) NOT NULL,
    event_timestamp DATETIME2(3) NOT NULL,
    payload_tonnes DECIMAL(6,2) NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);