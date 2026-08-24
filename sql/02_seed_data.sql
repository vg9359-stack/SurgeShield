-- Insert Sample Dam Location (Tehri Dam coordinates)
INSERT INTO dams (name, height_m, storage_volume_mcm, location)
VALUES (
    'Tehri Dam', 
    260.5, 
    3200.0, 
    ST_SetSRID(ST_MakePoint(78.0322, 30.3165), 4326)
);

-- Insert Downstream Village Settlements
INSERT INTO settlements (name, population, elevation_m, location) VALUES
('Rampur Village',        1450, 310.0, ST_SetSRID(ST_MakePoint(78.0600, 30.3250), 4326)),
('Govindpur',            3400, 285.5, ST_SetSRID(ST_MakePoint(78.1000, 30.3400), 4326)),
('Karanprayag Basti',    2100, 260.0, ST_SetSRID(ST_MakePoint(78.1250, 30.3550), 4326)),
('Devgram Settlement',   890,  340.2, ST_SetSRID(ST_MakePoint(78.0450, 30.3320), 4326)),
('Shanti Nagar',         5200, 240.8, ST_SetSRID(ST_MakePoint(78.1500, 30.3700), 4326)),
('Bhagirathi Colony',    1800, 295.0, ST_SetSRID(ST_MakePoint(78.0750, 30.3180), 4326)),
('Alaknanda Market',     4100, 230.5, ST_SetSRID(ST_MakePoint(78.1800, 30.3900), 4326)),
('Shivpuri Outpost',     650,  355.0, ST_SetSRID(ST_MakePoint(78.0200, 30.3450), 4326)),
('Ganges View Hub',      2900, 250.0, ST_SetSRID(ST_MakePoint(78.1350, 30.3620), 4326)),
('Nandprayag Hamlet',    420,  380.0, ST_SetSRID(ST_MakePoint(78.0100, 30.3600), 4326)),
('Rudra Enclave',        3100, 245.2, ST_SetSRID(ST_MakePoint(78.1650, 30.3800), 4326)),
('Saraswati Puram',      6300, 220.0, ST_SetSRID(ST_MakePoint(78.2100, 30.4100), 4326)),
('Koteshwar Valley',     1150, 305.4, ST_SetSRID(ST_MakePoint(78.0880, 30.3300), 4326)),
('Chamba Crossing',      2750, 270.1, ST_SetSRID(ST_MakePoint(78.1120, 30.3480), 4326)),
('Bhilangana Bank',      1950, 288.0, ST_SetSRID(ST_MakePoint(78.0550, 30.3050), 4326)),
('Srikot Village',       980,  325.6, ST_SetSRID(ST_MakePoint(78.0950, 30.3650), 4326)),
('Malitha Junction',     4800, 235.0, ST_SetSRID(ST_MakePoint(78.1920, 30.4000), 4326)),
('Pauri Foothills',      740,  395.0, ST_SetSRID(ST_MakePoint(78.0350, 30.3800), 4326)),
('Kirtinagar West',      3600, 255.8, ST_SetSRID(ST_MakePoint(78.1400, 30.3750), 4326)),
('Rishikesh North Sector', 8500, 210.0, ST_SetSRID(ST_MakePoint(78.2400, 30.4300), 4326));