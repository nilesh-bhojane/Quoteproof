import { useState, useEffect } from 'react';

const fmt = (n) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(n ?? 0);

function EditProductModal({ product, onSave, onClose }) {
  const [form, setForm] = useState({
    sell_price: product?.sell_price ?? '',
    cost_price: product?.cost_price ?? '',
    stock_on_hand: product?.stock_on_hand ?? 0,
    reserved: product?.reserved ?? 0,
  });
  const [saving, setSaving] = useState(false);

  function save() {
    setSaving(true);
    fetch(`/api/v1/products/${product.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sell_price: String(form.sell_price),
        cost_price: String(form.cost_price),
        stock_on_hand: Number(form.stock_on_hand),
        reserved: Number(form.reserved),
      }),
    })
      .then((r) => r.json())
      .then((updated) => onSave(updated))
      .catch(() => alert('Failed to save. Please retry.'))
      .finally(() => setSaving(false));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Edit Product</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <p className="modal-product-name">{product.name}</p>
        <div className="modal-fields">
          {[
            { key: 'sell_price', label: 'Sell Price (₹)' },
            { key: 'cost_price', label: 'Cost Price (₹)' },
            { key: 'stock_on_hand', label: 'Stock on Hand (pcs)' },
            { key: 'reserved', label: 'Reserved (pcs)' },
          ].map(({ key, label }) => (
            <div key={key} className="field-group">
              <label>{label}</label>
              <input
                type="number"
                min="0"
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            </div>
          ))}
        </div>
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={save} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
        <p className="muted" style={{ marginTop: 10 }}>
          Price edits set <code>price_updated_at</code> to now — resets the stale timer.
        </p>
      </div>
    </div>
  );
}

function AddProductModal({ onAdded, onClose }) {
  const [form, setForm] = useState({
    name: '',
    unit: 'pcs',
    sell_price: '',
    cost_price: '',
    min_margin_pct: '15',
    stock_on_hand: 0,
    track_stock: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function save() {
    if (!form.name.trim() || !form.sell_price || !form.cost_price) {
      setError('Name, Sell Price and Cost Price are required.');
      return;
    }
    setSaving(true);
    setError('');
    fetch('/api/v1/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: form.name.trim(),
        unit: form.unit,
        sell_price: String(form.sell_price),
        cost_price: String(form.cost_price),
        min_margin_pct: String(form.min_margin_pct),
        stock_on_hand: Number(form.stock_on_hand),
        track_stock: form.track_stock,
        aliases: [],
        bulk_tiers: [],
        reserved: 0,
      }),
    })
      .then((r) => {
        if (!r.ok) return r.json().then((e) => { throw new Error(JSON.stringify(e)); });
        return r.json();
      })
      .then((created) => onAdded(created))
      .catch((err) => setError('Failed: ' + err.message))
      .finally(() => setSaving(false));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Add New Product</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-fields">
          {[
            { key: 'name', label: 'Product Name', type: 'text' },
            { key: 'unit', label: 'Unit (pcs, kg, m…)', type: 'text' },
            { key: 'sell_price', label: 'Sell Price (₹)', type: 'number' },
            { key: 'cost_price', label: 'Cost Price (₹)', type: 'number' },
            { key: 'min_margin_pct', label: 'Min Margin %', type: 'number' },
            { key: 'stock_on_hand', label: 'Initial Stock', type: 'number' },
          ].map(({ key, label, type }) => (
            <div key={key} className="field-group">
              <label>{label}</label>
              <input
                type={type}
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            </div>
          ))}
          <div className="field-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.track_stock}
                onChange={(e) => setForm((f) => ({ ...f, track_stock: e.target.checked }))}
              />
              Track stock for this product
            </label>
          </div>
        </div>
        {error && <p className="error-banner" style={{ marginTop: 8 }}>⚠ {error}</p>}
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={save} disabled={saving}>
            {saving ? 'Adding…' : 'Add Product'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PriceListPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null);
  const [adding, setAdding] = useState(false);

  function load() {
    setLoading(true);
    fetch('/api/v1/products')
      .then((r) => r.json())
      .then((data) => setProducts(Array.isArray(data) ? data : []))
      .catch(() => setError('Could not load products. Is the backend running?'))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function handleSaved(updated) {
    setProducts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    setEditing(null);
  }

  function handleAdded(newProd) {
    setProducts((prev) => [...prev, newProd]);
    setAdding(false);
  }

  const staleCount = products.filter((p) => p.is_stale).length;
  const ooCount = products.filter((p) => p.track_stock && p.available_stock <= 0).length;

  return (
    <section className="page-section">
      <div className="page-header">
        <div>
          <p className="eyebrow">PART 1 · PERSON A</p>
          <h2>Price List &amp; Stock</h2>
          <p className="page-desc">Your live catalogue with real-time stock counts and stale-price alerts (updated &gt; 30 days ago).</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {staleCount > 0 && (
            <span className="stat-badge stat-badge--warn">⚠ {staleCount} stale price{staleCount > 1 ? 's' : ''}</span>
          )}
          {ooCount > 0 && (
            <span className="stat-badge stat-badge--oos">✗ {ooCount} out of stock</span>
          )}
          <button className="btn-primary" onClick={() => setAdding(true)}>+ Add Product</button>
          <button className="btn-secondary" onClick={load}>↻ Refresh</button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="panel">
        {loading ? (
          <p className="loading-text">Loading catalogue…</p>
        ) : products.length === 0 ? (
          <p className="muted">No products found. Add your first product above.</p>
        ) : (
          <div className="product-table">
            <div className="product-table__head">
              <span>Product</span>
              <span>Unit</span>
              <span>Sell Price</span>
              <span>Cost Price</span>
              <span>Available</span>
              <span>Stock</span>
              <span>Price Updated</span>
              <span></span>
            </div>
            {products.map((p) => {
              const stockPct = p.track_stock && p.stock_on_hand > 0
                ? Math.min(100, Math.round((p.available_stock / p.stock_on_hand) * 100))
                : null;

              return (
                <div
                  key={p.id}
                  className={`product-table__row${p.is_stale ? ' product-table__row--stale' : ''}`}
                >
                  <div>
                    <strong>{p.name}</strong>
                    {p.aliases && p.aliases.length > 0 && (
                      <small className="alias-list">{p.aliases.join(', ')}</small>
                    )}
                  </div>
                  <span>{p.unit}</span>
                  <span>{fmt(p.sell_price)}</span>
                  <span className="muted">{fmt(p.cost_price)}</span>
                  <div>
                    {p.track_stock ? (
                      <>
                        <strong
                          style={{
                            color:
                              p.available_stock <= 0
                                ? '#c0392b'
                                : p.available_stock < 50
                                ? '#e67e22'
                                : '#27ae60',
                          }}
                        >
                          {p.available_stock}
                        </strong>{' '}
                        <span className="muted">/ {p.stock_on_hand}</span>
                        {p.reserved > 0 && (
                          <small className="muted"> ({p.reserved} reserved)</small>
                        )}
                      </>
                    ) : (
                      <span className="muted">Untracked</span>
                    )}
                  </div>
                  <div>
                    {!p.track_stock ? (
                      <span className="stock-badge stock-badge--untracked">— Untracked</span>
                    ) : p.available_stock <= 0 ? (
                      <span className="stock-badge stock-badge--oos">✗ Out of Stock</span>
                    ) : p.available_stock < 50 ? (
                      <span className="stock-badge stock-badge--short">↓ Low Stock</span>
                    ) : (
                      <span className="stock-badge stock-badge--ok">✓ In Stock</span>
                    )}
                  </div>
                  <div>
                    {p.days_since_price_update != null ? (
                      <span className={p.is_stale ? 'stale-badge' : 'fresh-badge'}>
                        {p.is_stale ? '⚠ ' : ''}
                        {p.days_since_price_update}d ago
                      </span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </div>
                  <button className="btn-edit" onClick={() => setEditing(p)}>Edit</button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="legend">
        <span className="stock-badge stock-badge--ok">✓ In Stock</span>
        <span className="stock-badge stock-badge--short">↓ Low (&lt;50)</span>
        <span className="stock-badge stock-badge--oos">✗ Out of Stock</span>
        <span className="stale-badge">⚠ Stale (&gt;30d)</span>
        <span className="muted" style={{ fontSize: 11 }}>
          &nbsp;Stale prices show a warning before approval. Stock is never auto-reserved.
        </span>
      </div>

      {editing && (
        <EditProductModal product={editing} onSave={handleSaved} onClose={() => setEditing(null)} />
      )}
      {adding && (
        <AddProductModal onAdded={handleAdded} onClose={() => setAdding(false)} />
      )}
    </section>
  );
}
