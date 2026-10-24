import { useMemo, useState } from 'react';
export default function QuotationPanel() {
  const [largeQty, setLargeQty] = useState(500);
  const [unitPrice, setUnitPrice] = useState(24);
  const [taxRate, setTaxRate] = useState(18);
  const [approved, setApproved] = useState(false);
  const subtotal = useMemo(() => Math.max(0, Number(largeQty) || 0) * Math.max(0, Number(unitPrice) || 0), [largeQty, unitPrice]);
  const tax = subtotal * Math.max(0, Number(taxRate) || 0) / 100;
  const money = n => new Intl.NumberFormat('en-IN', {style:'currency',currency:'INR',maximumFractionDigits:2}).format(n);
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">CONTRIBUTOR B · VALIDATION & APPROVAL</p><h2>Quotation review</h2></div><span className={approved ? 'status success' : 'status warning'}>{approved ? 'Approved for demo' : 'Awaiting review'}</span></div>
    <div className="notice"><strong>Validation warning</strong><p>The smaller-box specification is unresolved. This demo total includes only the large-box line and must not be sent as a complete quotation.</p></div>
    <div className="table-head"><span>Item</span><span>Qty</span><span>Unit price</span><span>Line total</span></div>
    <div className="table-line"><div><strong>Large box</strong><small>12 × 10 × 8 · 3-ply · demo SKU</small></div><input aria-label="Quantity" type="number" min="0" value={largeQty} onChange={e=>{setLargeQty(e.target.value);setApproved(false);}}/><input aria-label="Unit price in rupees" type="number" min="0" value={unitPrice} onChange={e=>{setUnitPrice(e.target.value);setApproved(false);}}/><strong>{money(subtotal)}</strong></div>
    <div className="tax-row"><label>Tax rate (%) <input type="number" min="0" max="100" value={taxRate} onChange={e=>{setTaxRate(e.target.value);setApproved(false);}}/></label><div className="totals"><div><span>Subtotal</span><strong>{money(subtotal)}</strong></div><div><span>Tax</span><strong>{money(tax)}</strong></div><div className="grand-total"><span>Demo total</span><strong>{money(subtotal+tax)}</strong></div></div></div>
    <button className="primary" onClick={()=>setApproved(false)}>Save review changes</button> <button className="secondary" onClick={()=>setApproved(true)}>Approve demo line</button>
    <p className="muted">Demo calculation only. Tax rate and unit price are editable assumptions; unresolved lines must be completed before a real quote is approved.</p>
  </section>;
}
