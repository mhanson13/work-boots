-- Work Boots Console MVP schema
-- Postgres 14+

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE lead_source AS ENUM ('godaddy_email', 'phone_call', 'manual', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'qualified', 'quoted', 'won', 'lost', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE lead_event_type AS ENUM (
        'lead_received',
        'auto_ack_sent',
        'owner_notified',
        'owner_contacted',
        'appointment_set',
        'quote_sent',
        'status_changed',
        'won',
        'lost',
        'note_added'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE metric_source AS ENUM ('gbp', 'gbp_performance', 'ga4', 'search_console', 'ai_visibility');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_name TEXT,
    phone TEXT,
    email TEXT,
    timezone TEXT NOT NULL DEFAULT 'America/Denver',
    service_areas JSONB NOT NULL DEFAULT '[]'::jsonb,
    services JSONB NOT NULL DEFAULT '[]'::jsonb,
    godaddy_site_url TEXT,
    gbp_location_id TEXT,
    ga4_property_id TEXT,
    search_console_site_url TEXT,
    default_currency CHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    source lead_source NOT NULL DEFAULT 'godaddy_email',
    external_id TEXT,
    submitted_at TIMESTAMPTZ NOT NULL,
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    service_type TEXT,
    city TEXT,
    postal_code TEXT,
    message TEXT,
    status lead_status NOT NULL DEFAULT 'new',
    estimated_job_value NUMERIC(12,2),
    actual_job_value NUMERIC(12,2),
    first_response_at TIMESTAMPTZ,
    last_contacted_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_leads_business_status ON leads (business_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_business_submitted ON leads (business_id, submitted_at DESC);

CREATE TABLE IF NOT EXISTS lead_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    event_type lead_event_type NOT NULL,
    event_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_type TEXT NOT NULL DEFAULT 'system',
    actor_id TEXT,
    channel TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lead_events_lead_event_at ON lead_events (lead_id, event_at DESC);
CREATE INDEX IF NOT EXISTS idx_lead_events_business_event_at ON lead_events (business_id, event_at DESC);

CREATE TABLE IF NOT EXISTS visibility_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    source metric_source NOT NULL,
    profile_views INTEGER,
    map_views INTEGER,
    website_clicks INTEGER,
    phone_calls INTEGER,
    direction_requests INTEGER,
    search_impressions INTEGER,
    search_clicks INTEGER,
    avg_position NUMERIC(6,2),
    ai_answer_mentions INTEGER,
    ai_answer_share_pct NUMERIC(5,2),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id, metric_date, source)
);

CREATE INDEX IF NOT EXISTS idx_visibility_business_date ON visibility_metrics (business_id, metric_date DESC);

CREATE TABLE IF NOT EXISTS competitor_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    competitor_name TEXT NOT NULL,
    competitor_place_id TEXT,
    competitor_rating NUMERIC(3,2),
    competitor_review_count INTEGER,
    local_pack_rank INTEGER,
    share_of_voice_pct NUMERIC(5,2),
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_competitor_business_date ON competitor_snapshots (business_id, snapshot_date DESC);

CREATE TABLE IF NOT EXISTS marketing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    metric_period_start DATE NOT NULL,
    metric_period_end DATE NOT NULL,
    ad_spend NUMERIC(12,2) NOT NULL DEFAULT 0,
    leads_total INTEGER NOT NULL DEFAULT 0,
    leads_marketing INTEGER NOT NULL DEFAULT 0,
    jobs_won INTEGER NOT NULL DEFAULT 0,
    revenue_from_jobs NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_job_value NUMERIC(12,2),
    cost_per_lead NUMERIC(12,2),
    cost_per_job NUMERIC(12,2),
    response_time_minutes NUMERIC(10,2),
    romi_pct NUMERIC(8,2),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id, metric_period_start, metric_period_end)
);

CREATE INDEX IF NOT EXISTS idx_marketing_business_period ON marketing_metrics (business_id, metric_period_start DESC);
