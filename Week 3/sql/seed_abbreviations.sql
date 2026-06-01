-- Default abbreviation seeds — run after schema.sql
-- Lookup is case-insensitive in Python (brclt == BRCLT, pg == PG).

INSERT INTO abbreviations (abbreviation, full_term, field_category) VALUES
-- Bracelet
('BRCLT',  'BRACELET',       'bracelet'),
('BRACE',  'BRACELET',       'bracelet'),
('LEATH',  'LEATHER STRAP',  'bracelet'),
('MECH',   'MESH',           'bracelet'),
('JEW',    'JEWELLERY STRAP', 'bracelet'),
-- Color
('YG',     'YELLOW GOLD',    'color'),
('RG',     'ROSE GOLD',      'color'),
('PG',     'PINK GOLD',      'color'),
('SS',     'STAINLESS STEEL', 'color'),
('BK',     'BLACK',          'color'),
('WH',     'WHITE',          'color'),
-- Movement
('AUTO',   'AUTOMATIC',      'movement')
ON CONFLICT (abbreviation, field_category) DO NOTHING;
