import { useState } from 'react';
import InquiryPanel from './features/inquiry/InquiryPanel.jsx';
import QuotationPanel from './features/quotation/QuotationPanel.jsx';
import AnalyticsPanel from './features/analytics/AnalyticsPanel.jsx';

export default function App() {
  const [active, setActive] = useState('Inquiry');
  const tabs = ['Inquiry', 'Quotation', 'Evidence & ROI'];
  return <main className="shell">
    <header className="topbar"><div className="brand-mark">Q</div><div><div className="brand">QuoteProof <span>AI</span></div><div className="subtitle">AI-assisted quotations. Evidence-backed productivity.</div></div><div className="demo-pill">HACKATHON DEMO</div></header>
    <section className="intro"><div><p className="eyebrow">QUOTE WORKSPACE</p><h1>Make every quotation <em>accountable.</em></h1><p className="lede">Turn messy inquiries into reviewed quote drafts, while recording the decisions and time behind each one.</p></div><div className="step-card"><div className="step-label">WORKFLOW</div><div>01&nbsp; Intake</div><div>02&nbsp; Validate</div><div>03&nbsp; Approve & measure</div></div></section>
    <nav className="tabs">{tabs.map(tab => <button key={tab} className={active === tab ? 'tab active' : 'tab'} onClick={() => setActive(tab)}>{tab}</button>)}</nav>
    {active === 'Inquiry' && <InquiryPanel />}
    {active === 'Quotation' && <QuotationPanel />}
    {active === 'Evidence & ROI' && <AnalyticsPanel />}
    <footer>Prototype mode · Use synthetic data · Verify every quotation before sending</footer>
  </main>;
}
