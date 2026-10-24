import { useState } from 'react';
import NewQuotePage from './pages/new-quote/NewQuotePage.jsx';
import PriceListPage from './pages/price-list/PriceListPage.jsx';
import QuotationPanel from './features/quotation/QuotationPanel.jsx';
import AnalyticsPanel from './features/analytics/AnalyticsPanel.jsx';
import SettingsPanel from './features/settings/SettingsPanel.jsx';

// Section 12 screens: New Quote · Quotes · Price List & Stock · Reports · Settings
const TABS = [
  { id: 'new-quote',  label: '✦ New Quote',          owner: 'A' },
  { id: 'quotation',  label: '📋 Quotation Review',   owner: 'B' },
  { id: 'price-list', label: '📦 Price List & Stock',  owner: 'A' },
  { id: 'reports',    label: '📊 Reports & Evidence',  owner: 'B' },
  { id: 'settings',   label: '⚙ Settings',            owner: 'B' },
];

export default function App() {
  const [active, setActive] = useState('new-quote');
  const [draftForReview, setDraftForReview] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);

  function handleSendToReview(draft) {
    // Map /api/v1 draft response to QuotationPanel's expected shape (Handshake)
    const items = (draft.items || []).map((it) => ({
      description: it.description || it.raw_text,
      sku: it.product_id || null,
      quantity: Number(it.qty),
      unitPrice: Number(it.unit_price_snapshot || 0),
      matched: !!it.product_id,
    }));
    setDraftForReview(items);

    const event = {
      id: `evt-${Date.now()}`,
      event_type: 'draft_created',
      title: 'Draft sent from New Quote to Review',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: `Transferred ${items.length} line item(s), total ₹${Number(draft.total).toFixed(2)}`,
    };
    setAuditEvents((prev) => [event, ...prev]);
    setActive('quotation');
  }

  function handleRecordEvent(event) {
    setAuditEvents((prev) => [event, ...prev]);
  }

  function handleDataReset() {
    setDraftForReview(null);
    setAuditEvents([]);
  }

  return (
    <main className="shell">
      {/* ── Top bar ── */}
      <header className="topbar">
        <div className="brand-mark">Q</div>
        <div>
          <div className="brand">
            QuoteProof <span>AI</span>
          </div>
          <div className="subtitle">
            AI reads · code calculates · human approves · ledger proves
          </div>
        </div>
        <div className="demo-pill">PRAGYAN 2K26 · PS 4-01</div>
      </header>

      {/* ── Nav tabs ── */}
      <nav className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={active === tab.id ? 'tab active' : 'tab'}
            onClick={() => setActive(tab.id)}
          >
            {tab.label}
            <span className={`tab-owner tab-owner--${tab.owner.toLowerCase()}`}>
              {tab.owner}
            </span>
          </button>
        ))}
      </nav>

      {/* ── Page content ── */}
      {active === 'new-quote' && (
        <NewQuotePage onSendToReview={handleSendToReview} />
      )}
      {active === 'quotation' && (
        <QuotationPanel
          initialItems={draftForReview}
          onRecordEvent={handleRecordEvent}
        />
      )}
      {active === 'price-list' && (
        <PriceListPage />
      )}
      {active === 'reports' && (
        <AnalyticsPanel externalEvents={auditEvents} />
      )}
      {active === 'settings' && (
        <SettingsPanel onDataReset={handleDataReset} />
      )}

      <footer>
        Prototype · Synthetic data only · Verify every quotation before sending ·{' '}
        <span className="muted">PII masked before AI</span>
      </footer>
    </main>
  );
}
