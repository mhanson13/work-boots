-- Minimal seed for local dashboard testing

INSERT INTO businesses (
    id,
    name,
    slug,
    owner_name,
    phone,
    email,
    service_areas,
    services,
    godaddy_site_url,
    gbp_location_id,
    ga4_property_id,
    search_console_site_url
)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'T&M Fire',
    'tm-fire',
    'Matt Hansen',
    '+1-303-555-0100',
    'owner@tmfire.example',
    '["Denver", "Aurora", "Lakewood"]'::jsonb,
    '["fire restoration", "smoke cleanup", "water mitigation"]'::jsonb,
    'https://tmfire.example',
    '1234567890',
    '987654321',
    'sc-domain:tmfire.example'
)
ON CONFLICT (slug) DO NOTHING;
