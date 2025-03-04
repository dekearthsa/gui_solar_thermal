USE solarthermal;

CREATE TABLE IF NOT EXISTS sun_path (
    id INT AUTO_INCREMENT PRIMARY KEY,
    heliostats_id VARCHAR(6),
    timestamp_s: VARCHAR(25),
    string_date: VARCHAR(25),
    is_day: VARCHAR(2),
    is_month: VARCHAR(2),
    is_year: VARCHAR(4),
    camera: VARCHAR(25),
    altitude: FLOAT,
    azimuth: FLOAT,
    -- declination: FLOAT,
    -- hour_angle: FLOAT,
    radiation: FLOAT,
    x: FLOAT,
    y: FLOAT,
);
