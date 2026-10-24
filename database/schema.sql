-- ==============================================================================
-- QuoteProof AI — Database Schema
-- Supabase Postgres Schema per CONTEXT.md Section 10
-- ==============================================================================

-- Enable UUID extension if not already present
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Clean drop for idempotency in dev/test
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS timings CASCADE;
DROP TABLE IF EXISTS ai_usage CASCADE;
DROP TABLE IF EXISTS quote_items CASCADE;
DROP TABLE IF EXISTS quotes CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

-- ------------------------------------------------------------------------------
-- 1. PRODUCTS
-- Catalog items with cost price, selling price, margins, and stock counters
-- ------------------------------------------------------------------------------
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    unit TEXT NOT NULL DEFAULT 'pcs',
    sell_price NUMERIC(12, 2) NOT NULL,
    cost_price NUMERIC(12, 2) NOT NULL,
    min_margin_pct NUMERIC(5, 2) NOT NULL DEFAULT 15.00,
    bulk_tiers JSONB NOT NULL DEFAULT '[]'::jsonb,
    stock_on_hand INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    track_stock BOOLEAN NOT NULL DEFAULT true,
    price_updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 2. QUOTES
-- Top-level quotation document
-- ------------------------------------------------------------------------------
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'rejected')),
    inquiry_masked TEXT NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    gst NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 3. QUOTE_ITEMS
-- Line items within a quotation with price snapshot and validation flags
-- ------------------------------------------------------------------------------
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    raw_text TEXT NOT NULL,
    qty NUMERIC(12, 2) NOT NULL DEFAULT 1.00,
    unit TEXT NOT NULL DEFAULT 'pcs',
    unit_price_snapshot NUMERIC(12, 2),
    line_total NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    ai_proposed JSONB NOT NULL DEFAULT '{}'::jsonb,
    final JSONB NOT NULL DEFAULT '{}'::jsonb,
    flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    stock_status TEXT NOT NULL DEFAULT 'ok' CHECK (stock_status IN ('ok', 'short', 'out_of_stock', 'untracked')),
    explain_text TEXT
);

-- ------------------------------------------------------------------------------
-- 4. AUDIT_LOG
-- Append-only evidence ledger of system, AI, and human review actions
-- ------------------------------------------------------------------------------
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id TEXT,
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    actor TEXT NOT NULL CHECK (actor IN ('ai', 'human', 'system')),
    action TEXT NOT NULL,
    before JSONB NOT NULL DEFAULT '{}'::jsonb,
    after JSONB NOT NULL DEFAULT '{}'::jsonb,
    at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 5. TIMINGS
-- Measured or estimated time recorded per quote for verifiable ROI
-- ------------------------------------------------------------------------------
CREATE TABLE timings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('manual', 'assisted')),
    seconds NUMERIC(10, 2) NOT NULL,
    at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 6. AI_USAGE
-- Token and INR cost tracking per quote request
-- ------------------------------------------------------------------------------
CREATE TABLE ai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    cost_inr NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 7. SETTINGS
-- Single-row configuration for business rules and defaults
-- ------------------------------------------------------------------------------
CREATE TABLE settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    hourly_rate NUMERIC(12, 2) NOT NULL DEFAULT 300.00,
    stale_days INTEGER NOT NULL DEFAULT 30,
    gst_pct NUMERIC(5, 2) NOT NULL DEFAULT 18.00,
    basic_mode BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Enabled on all 7 tables per CONTEXT.md requirements
-- ==============================================================================
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE timings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Standard demo policies allowing access for app operations
CREATE POLICY "Allow all operations on products" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on quotes" ON quotes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on quote_items" ON quote_items FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on audit_log" ON audit_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on timings" ON timings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on ai_usage" ON ai_usage FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on settings" ON settings FOR ALL USING (true) WITH CHECK (true);

-- Indexes for performance
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_quote_items_quote_id ON quote_items(quote_id);
CREATE INDEX idx_audit_log_quote_id ON audit_log(quote_id);
CREATE INDEX idx_timings_quote_id ON timings(quote_id);
CREATE INDEX idx_ai_usage_quote_id ON ai_usage(quote_id);
