USE solarthermal;

CREATE TABLE IF NOT EXISTS solar_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    heliostats_id VARCHAR(255), --
    timestamp_s: VARCHAR(255),
    string_date: VARCHAR(255), --
    is_day:INT,
    is_month:INT,
    is_year:INT,
    is_lat: FLOAT,
    is_lng: FLOAT,
    camera: VARCHAR(255), --
    altitude: FLOAT,  -- 
    azimuth_gyro: FLOAT, --
    elevation_gyro: FLOAT, --
    azimuth: FLOAT, -- preprocess before training 
    declination: FLOAT,  -- preprocess before training 
    hour_angle: FLOAT, -- preprocess before training 
    radiation: FLOAT, -- preprocess before training 
    x_angle: FLOAT, -- ตำแหน่งซ้่ายขวาจาก  helostats จาก tower 
    y_angle: FLOAT, -- ความสไกลใกล้ helostats จาก tower
    z_angle: FLOAT, -- ความสูง  helostats จาก tower 
    target_angle: FLOAT, -- มุมกดเป้า
    high_tower: FLOAT, -- ความสูงเป้า
    x: FLOAT,
    y: FLOAT,
);
