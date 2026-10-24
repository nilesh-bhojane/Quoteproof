import React, { useEffect } from 'react';

export default function QuotationPanel() {
  // Load static price list (could be from an API in real app)
  const [priceList, setPriceList] = React.useState([]);
  const [items, setItems] = React.useState([
    { description: 'Large box', sku: 'DEMO001', qty: 500, unitPrice: 24 },
    { description: 'Small box', sku: 'SMALL001', qty: 0, unitPrice: 12 }
  ]);
  const [taxRate, setTaxRate] = React.useState(18);
  const [approved, setApproved] = React.useState(false);

  // Load price list JSON placed under src/data
  useEffect(() => {
    import('../data/priceList.json')
      .then(mod => setPriceList(mod.default))
      .catch(() => setPriceList([]));
  }, []);

  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = Number(value);
    setItems(newItems);
    setApproved(false);
  };

  const subtotal = items.reduce((sum, it) => sum + (it.qty || 0) * (it.unitPrice || 0), 0);
  const tax = subtotal * Math.max(0, Number(taxRate) || 0) / 100;
  const money = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(n);
  const canApprove = items.every(it => it.qty > 0 && it.unitPrice > 0);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CONTRIBUTOR B · VALIDATION & APPROVAL</p>
          <h2>Quotation review</h2>
        </div>
        <span className={approved ? 'status success' : 'status warning'}>
          {approved ? 'Approved for demo' : 'Awaiting review'}
        </span>
      </div>

      <div className="notice">
        <strong>Validation warning</strong>
        <p>All items must have quantity and unit price before approval.</p>
      </div>

      <div className="table-head">
        <span>Item</span><span>Qty</span><span>Unit price</span><span>Line total</span>
      </div>
      {items.map((it, idx) => (
        <div className="table-line" key={it.sku}>
          <div><strong>{it.description}</strong><small>{it.sku}</small></div>
          <input aria-label="Quantity" type="number" min="0" value={it.qty}
                 onChange={e => updateItem(idx, 'qty', e.target.value)} />
          <input aria-label="Unit price in rupees" type="number" min="0" value={it.unitPrice}
                 onChange={e => updateItem(idx, 'unitPrice', e.target.value)} />
          <strong>{money(it.qty * it.unitPrice)}</strong>
        </div>
      ))}

      <div className="tax-row">
        <label>Tax rate (%)
          <input type="number" min="0" max="100" value={taxRate}
                 onChange={e => { setTaxRate(e.target.value); setApproved(false); }} />
        </label>
        <div className="totals">
          <div><span>Subtotal</span><strong>{money(subtotal)}</strong></div>
          <div><span>Tax</span><strong>{money(tax)}</strong></div>
          <div className="grand-total"><span>Demo total</span><strong>{money(subtotal + tax)}</strong></div>
        </div>
      </div>

      <button className="primary" onClick={() => setApproved(false)}>Save review changes</button>
      <button className="secondary" disabled={!canApprove} onClick={() => setApproved(true)}>Approve demo line</button>

      <p className="muted">Demo calculation only. Tax rate and unit price are editable assumptions; unresolved lines must be completed before a real quote is approved.</p>
    </section>
  );
}
