-- ==============================================================================
-- QuoteProof AI — Database Seed Data
-- Seed data for Person B per CONTEXT.md Section 9 & 10
-- ==============================================================================

-- Clean existing data before seeding
TRUNCATE TABLE audit_log, timings, ai_usage, quote_items, quotes, products RESTART IDENTITY CASCADE;

-- ------------------------------------------------------------------------------
-- 1. SETTINGS (Default business settings)
-- ------------------------------------------------------------------------------
INSERT INTO settings (id, hourly_rate, stale_days, gst_pct, basic_mode, updated_at)
VALUES (1, 300.00, 30, 18.00, false, now())
ON CONFLICT (id) DO UPDATE SET
    hourly_rate = EXCLUDED.hourly_rate,
    stale_days = EXCLUDED.stale_days,
    gst_pct = EXCLUDED.gst_pct,
    basic_mode = EXCLUDED.basic_mode,
    updated_at = now();

-- ------------------------------------------------------------------------------
-- 2. PRODUCTS (8 packaging products with specific edge-case scenarios)
-- ------------------------------------------------------------------------------
-- Product 1: Plenty of stock (Regular 3-Ply box)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Corrugated Box 12x10x8 (3-Ply)',
    ARRAY['box 12x10x8', 'carton 12x10x8', 'standard shipping box', '3-ply box'],
    'pcs',
    24.00,
    18.00,
    15.00,
    '[{"min_qty": 500, "unit_price": 22.00}, {"min_qty": 2000, "unit_price": 20.00}]'::jsonb,
    5000,
    0,
    true,
    now()
);

-- Product 2: Exactly 120 available (for Section 14 demo: 500 requested, 120 available)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'Heavy Duty Box 18x14x12 (5-Ply)',
    ARRAY['5-ply box', 'heavy duty carton', 'box 18x14x12', 'large box'],
    'pcs',
    48.00,
    36.00,
    20.00,
    '[{"min_qty": 200, "unit_price": 44.00}]'::jsonb,
    120,
    0,
    true,
    now()
);

-- Product 3: Zero stock (Out of stock case)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000003',
    'Die-Cut Mailer Box 10x8x3 (White E-Flute)',
    ARRAY['white mailer', 'mailer box', 'e-commerce box', 'die cut box'],
    'pcs',
    32.00,
    24.00,
    20.00,
    '[]'::jsonb,
    0,
    0,
    true,
    now()
);

-- Product 4: 60-day-old price (Triggers stale-price warning > 30 days)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000004',
    'Air Bubble Roll 100m x 1m (50 GSM)',
    ARRAY['bubble wrap', 'bubble roll', 'air bubble packaging'],
    'roll',
    850.00,
    680.00,
    15.00,
    '[{"min_qty": 10, "unit_price": 800.00}]'::jsonb,
    80,
    0,
    true,
    now() - INTERVAL '60 days'
);

-- Product 5: track_stock = false (Untracked service / made-to-order packaging)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000005',
    'Custom Brand Logo Printing (1-Color Screen)',
    ARRAY['logo printing', 'screen print', 'brand printing'],
    'job',
    1200.00,
    600.00,
    40.00,
    '[]'::jsonb,
    0,
    0,
    false,
    now()
);

-- Product 6: BOPP Packaging Tape Roll (65m, Brown)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000006',
    'BOPP Brown Packaging Tape (48mm x 65m)',
    ARRAY['brown tape', 'bopp tape', 'packing tape', 'carton tape'],
    'roll',
    65.00,
    48.00,
    20.00,
    '[{"min_qty": 72, "unit_price": 58.00}]'::jsonb,
    600,
    0,
    true,
    now()
);

-- Product 7: Stretch Wrapping Film Roll (23 Micron, 4kg)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000007',
    'Manual Stretch Film Roll (4kg, 23 Micron)',
    ARRAY['stretch film', 'pallet wrap', 'cling film packaging'],
    'roll',
    620.00,
    510.00,
    15.00,
    '[{"min_qty": 20, "unit_price": 580.00}]'::jsonb,
    150,
    10,
    true,
    now()
);

-- Product 8: Corrugated Partition Sheets (3-Ply 12x10)
INSERT INTO products (id, name, aliases, unit, sell_price, cost_price, min_margin_pct, bulk_tiers, stock_on_hand, reserved, track_stock, price_updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000008',
    'Corrugated Partition Dividers 12x10',
    ARRAY['partition', 'box divider', 'separator sheet'],
    'pcs',
    8.50,
    6.00,
    25.00,
    '[{"min_qty": 1000, "unit_price": 7.50}]'::jsonb,
    2500,
    0,
    true,
    now()
);

-- ------------------------------------------------------------------------------
-- 3. THREE SAMPLE QUOTES (For Person B's testing)
-- ------------------------------------------------------------------------------

-- Quote 1: DRAFT (Pending Review, with short-stock warning on Item 2)
INSERT INTO quotes (id, status, inquiry_masked, subtotal, gst, total, approved_by, approved_at, created_at)
VALUES (
    '10000000-0000-0000-0000-000000000001',
    'draft',
    'Need urgent quote for 500 boxes 12x10x8 and 500 heavy duty 5-ply cartons. Delivery to Pune next Tuesday. Contact: [NAME_1], [PHONE_1]',
    33000.00,
    5940.00,
    38940.00,
    NULL,
    NULL,
    now() - INTERVAL '30 minutes'
);

INSERT INTO quote_items (id, quote_id, product_id, raw_text, qty, unit, unit_price_snapshot, line_total, ai_proposed, final, flags, stock_status, explain_text)
VALUES
(
    '11000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '500 boxes 12x10x8',
    500.00,
    'pcs',
    22.00,
    11000.00,
    '{"qty": 500, "sku": "BOX-3PLY"}'::jsonb,
    '{"qty": 500, "unit_price": 22.00}'::jsonb,
    '[]'::jsonb,
    'ok',
    'Applied tier pricing for >= 500 units (Rs 22/pc vs standard Rs 24/pc).'
),
(
    '11000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    '500 heavy duty 5-ply cartons',
    500.00,
    'pcs',
    44.00,
    22000.00,
    '{"qty": 500, "sku": "BOX-5PLY"}'::jsonb,
    '{"qty": 500, "unit_price": 44.00}'::jsonb,
    '[{"code": "STOCK_SHORT", "severity": "blocking", "message": "Only 120 available in stock; 500 requested.", "suggested_action": "Quote partial qty (120) or schedule backorder.", "blocks_approval": true}]'::jsonb,
    'short',
    'Stock shortage: 120 available on hand, 380 backorder required.'
);

-- Quote 2: APPROVED (Completed quotation with owner approval and snapshot)
INSERT INTO quotes (id, status, inquiry_masked, subtotal, gst, total, approved_by, approved_at, created_at)
VALUES (
    '10000000-0000-0000-0000-000000000002',
    'approved',
    'Please send 100 rolls brown packaging tape and 10 rolls stretch wrap to Bhosari MIDC. Email: [EMAIL_1]',
    11600.00,
    2088.00,
    13688.00,
    'Rajesh Mehta',
    now() - INTERVAL '2 hours',
    now() - INTERVAL '3 hours'
);

INSERT INTO quote_items (id, quote_id, product_id, raw_text, qty, unit, unit_price_snapshot, line_total, ai_proposed, final, flags, stock_status, explain_text)
VALUES
(
    '11000000-0000-0000-0000-000000000003',
    '10000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000006',
    '100 rolls brown packaging tape',
    100.00,
    'roll',
    58.00,
    5800.00,
    '{"qty": 100, "sku": "TAPE-BROWN"}'::jsonb,
    '{"qty": 100, "unit_price": 58.00}'::jsonb,
    '[]'::jsonb,
    'ok',
    'Bulk tier applied for >= 72 rolls.'
),
(
    '11000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000007',
    '10 rolls stretch wrap',
    10.00,
    'roll',
    580.00,
    5800.00,
    '{"qty": 10, "sku": "STRETCH-4KG"}'::jsonb,
    '{"qty": 10, "unit_price": 580.00}'::jsonb,
    '[]'::jsonb,
    'ok',
    'Standard rate (Rs 580.00/roll).'
);

-- Quote 3: REJECTED (Out of stock item declined by customer or owner)
INSERT INTO quotes (id, status, inquiry_masked, subtotal, gst, total, approved_by, approved_at, created_at)
VALUES (
    '10000000-0000-0000-0000-000000000003',
    'rejected',
    'Need 1000 pcs white die-cut mailer boxes for tomorrow morning pickup.',
    0.00,
    0.00,
    0.00,
    NULL,
    NULL,
    now() - INTERVAL '1 day'
);

INSERT INTO quote_items (id, quote_id, product_id, raw_text, qty, unit, unit_price_snapshot, line_total, ai_proposed, final, flags, stock_status, explain_text)
VALUES (
    '11000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000003',
    '00000000-0000-0000-0000-000000000003',
    '1000 pcs white die-cut mailer boxes',
    1000.00,
    'pcs',
    32.00,
    0.00,
    '{"qty": 1000, "sku": "MAILER-WHITE"}'::jsonb,
    '{"qty": 1000, "declined": true}'::jsonb,
    '[{"code": "OUT_OF_STOCK", "severity": "blocking", "message": "Product is completely out of stock with zero available inventory.", "suggested_action": "Decline quote or offer alternative box.", "blocks_approval": true}]'::jsonb,
    'out_of_stock',
    'Item out of stock; owner declined quote.'
);

-- ------------------------------------------------------------------------------
-- 4. AUDIT_LOG (Evidence Ledger events for the 3 sample quotes)
-- ------------------------------------------------------------------------------
-- Events for Quote 1 (Draft flow)
INSERT INTO audit_log (id, correlation_id, quote_id, actor, action, before, after, at)
VALUES
(
    '20000000-0000-0000-0000-000000000001',
    'corr-q1-001',
    '10000000-0000-0000-0000-000000000001',
    'ai',
    'draft_extracted',
    '{}'::jsonb,
    '{"items_extracted": 2, "masked_input": true}'::jsonb,
    now() - INTERVAL '30 minutes'
),
(
    '20000000-0000-0000-0000-000000000002',
    'corr-q1-002',
    '10000000-0000-0000-0000-000000000001',
    'system',
    'flags_raised',
    '{}'::jsonb,
    '{"flags": ["STOCK_SHORT"]}'::jsonb,
    now() - INTERVAL '29 minutes'
);

-- Events for Quote 2 (Full review and approval flow)
INSERT INTO audit_log (id, correlation_id, quote_id, actor, action, before, after, at)
VALUES
(
    '20000000-0000-0000-0000-000000000003',
    'corr-q2-001',
    '10000000-0000-0000-0000-000000000002',
    'ai',
    'draft_extracted',
    '{}'::jsonb,
    '{"items_extracted": 2}'::jsonb,
    now() - INTERVAL '3 hours'
),
(
    '20000000-0000-0000-0000-000000000004',
    'corr-q2-002',
    '10000000-0000-0000-0000-000000000002',
    'human',
    'line_item_adjusted',
    '{"tape_qty": 100, "unit_price": 65.00}'::jsonb,
    '{"tape_qty": 100, "unit_price": 58.00, "reason": "applied tier rate"}'::jsonb,
    now() - INTERVAL '2 hours 15 minutes'
),
(
    '20000000-0000-0000-0000-000000000005',
    'corr-q2-003',
    '10000000-0000-0000-0000-000000000002',
    'human',
    'quote_approved',
    '{"status": "draft"}'::jsonb,
    '{"status": "approved", "approved_by": "Rajesh Mehta"}'::jsonb,
    now() - INTERVAL '2 hours'
);

-- Events for Quote 3 (Rejection flow)
INSERT INTO audit_log (id, correlation_id, quote_id, actor, action, before, after, at)
VALUES
(
    '20000000-0000-0000-0000-000000000006',
    'corr-q3-001',
    '10000000-0000-0000-0000-000000000003',
    'human',
    'quote_rejected',
    '{"status": "draft"}'::jsonb,
    '{"status": "rejected", "reason": "out_of_stock"}'::jsonb,
    now() - INTERVAL '23 hours'
);

-- ------------------------------------------------------------------------------
-- 5. TIMINGS (Measured sample timings for Evidence & ROI)
-- ------------------------------------------------------------------------------
INSERT INTO timings (id, quote_id, kind, seconds, at)
VALUES
('30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000002', 'assisted', 185.00, now() - INTERVAL '2 hours'),
('30000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'manual', 650.00, now() - INTERVAL '2 hours');

-- ------------------------------------------------------------------------------
-- 6. AI_USAGE (Token and cost tracking for Quote 1 & 2)
-- ------------------------------------------------------------------------------
INSERT INTO ai_usage (id, quote_id, tokens_in, tokens_out, cost_inr, created_at)
VALUES
('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 342, 128, 0.45, now() - INTERVAL '30 minutes'),
('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 290, 95, 0.38, now() - INTERVAL '3 hours');
