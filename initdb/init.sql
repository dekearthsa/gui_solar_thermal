USE solarthermal;

CREATE TABLE IF NOT EXISTS solar_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    heliostats_id VARCHAR(255),
    timestamp_s: VARCHAR(255),
    string_date: VARCHAR(255),
    is_day:INT,
    is_month:INT,
    is_year:INT,
    camera: VARCHAR(255),
    altitude: FLOAT,
    azimuth_gyro: FLOAT,
    elevation_gyro: FLOAT,
    azimuth: FLOAT,
    declination: FLOAT,
    hour_angle: FLOAT,
    radiation: FLOAT,
    x: FLOAT,
    y: FLOAT,
);
