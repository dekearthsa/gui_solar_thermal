USE mydatabase;

CREATE TABLE IF NOT EXISTS airQuality (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp_s: VARCHAR(25),
    string_date: VARCHAR(25),
    camera: VARCHAR(25),
    altitude: FLOAT,
    azimuth: FLOAT,
    declination: FLOAT,
    hour_angle: FLOAT,
    radiation: FLOAT,
    x: FLOAT,
    y: FLOAT,
);
