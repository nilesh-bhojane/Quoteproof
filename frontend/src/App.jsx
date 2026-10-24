import { useState } from 'react';
import InquiryPanel from './features/inquiry/InquiryPanel.jsx';
import QuotationPanel from './features/quotation/QuotationPanel.jsx';
import ProductsPanel from './features/products/ProductsPanel.jsx';
import AnalyticsPanel from './features/analytics/AnalyticsPanel.jsx';
import SettingsPanel from './features/settings/SettingsPanel.jsx';

export default function App() {
  const [active, setActive] = useState('New Quote');
  const [transferredItems, setTransferredItems] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);

  // CONTEXT.md Section 12: 5 Core Screens
  const tabs = ['New Quote', 'Price list & stock', 'Reports & Proof', 'Settings'];

  function handleTransferToQuote(items) {
    setTransferredItems(items);
    const event = {
      id: `evt-${Date.now()}`,
      event_type: 'draft_created',
      title: 'Quote draft created from inquiry intake',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: `Transferred ${items.length} line items to quotation review`,
    };
    setAuditEvents(prev => [event, ...prev]);
    setActive('New Quote');
  }

  function handleRecordEvent(event) {
    setAuditEvents(prev => [event, ...prev]);
  }

  function handleDataReset() {
    setTransferredItems(null);
    setAuditEvents([]);
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark">Q</div>
        <div>
          <div className="brand">
            QuoteProof <span>AI</span>
          </div>
          <div className="subtitle">
            AI-assisted quotations. Evidence-backed productivity.
          </div>
        </div>
        <div className="demo-pill">PRAGYAN 2K26 · PS 4-01</div>
      </header>

      <section className="intro">
        <div>
          <p className="eyebrow">QUOTE WORKSPACE</p>
          <h1>
            Make every quotation <em>accountable.</em>
          </h1>
          <p className="lede">
            Turn messy inquiries into reviewed quote drafts, while recording the decisions and time behind each one.
          </p>
        </div>
        <div className="step-card">
          <div className="step-label">WORKFLOW</div>
          <div>01&nbsp; Intake & Mask PII</div>
          <div>02&nbsp; Match & Stock Check</div>
          <div>03&nbsp; Approve & Measure ROI</div>
        </div>
      </section>

      <nav className="tabs">
        {tabs.map(tab => (
          <button
            key={tab}
            className={active === tab ? 'tab active' : 'tab'}
            onClick={() => setActive(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      {active === 'New Quote' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <InquiryPanel onTransferToQuote={handleTransferToQuote} />
          <QuotationPanel
            initialItems={transferredItems}
            onRecordEvent={handleRecordEvent}
          />
        </div>
      )}

      {active === 'Price list & stock' && (
        <ProductsPanel />
      )}

      {active === 'Reports & Proof' && (
        <AnalyticsPanel externalEvents={auditEvents} />
      )}

      {active === 'Settings' && (
        <SettingsPanel onDataReset={handleDataReset} />
      )}

      <footer>
        Prototype mode · Use synthetic data · Verify every quotation before sending
      </footer>
    </main>
  );
}
