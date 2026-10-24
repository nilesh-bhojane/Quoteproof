import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import PriceListPage from './PriceListPage.jsx';

const MOCK_PRODUCTS = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'Corrugated Box 12x10x8 (3-Ply)',
    aliases: ['box 12x10x8', '3-ply box'],
    unit: 'pcs',
    sell_price: '24.00',
    cost_price: '18.00',
    min_margin_pct: '15.00',
    bulk_tiers: [{ min_qty: 500, unit_price: '22.00' }],
    stock_on_hand: 5000,
    reserved: 0,
    available_stock: 5000,
    track_stock: true,
    price_updated_at: new Date().toISOString(),
    is_stale: false,
    days_since_price_update: 0,
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    name: 'Heavy Duty Box 18x14x12 (5-Ply)',
    aliases: ['5-ply box', 'heavy duty carton'],
    unit: 'pcs',
    sell_price: '48.00',
    cost_price: '36.00',
    min_margin_pct: '20.00',
    bulk_tiers: [],
    stock_on_hand: 120,
    reserved: 0,
    available_stock: 120,
    track_stock: true,
    price_updated_at: '2026-09-01T00:00:00Z',
    is_stale: true,
    days_since_price_update: 54,
  },
  {
    id: '00000000-0000-0000-0000-000000000003',
    name: 'Die-Cut Mailer Box (White E-Flute)',
    aliases: ['white mailer'],
    unit: 'pcs',
    sell_price: '32.00',
    cost_price: '24.00',
    min_margin_pct: '20.00',
    bulk_tiers: [],
    stock_on_hand: 0,
    reserved: 0,
    available_stock: 0,
    track_stock: true,
    price_updated_at: new Date().toISOString(),
    is_stale: false,
    days_since_price_update: 0,
  },
];

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(MOCK_PRODUCTS),
  });
});

describe('PriceListPage', () => {
  it('renders page heading', async () => {
    render(<PriceListPage />);
    expect(screen.getByText(/Price List & Stock/i)).toBeTruthy();
  });

  it('fetches and displays products', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Corrugated Box 12x10x8/i)).toBeTruthy();
      expect(screen.getByText(/Heavy Duty Box/i)).toBeTruthy();
    });
  });

  it('shows stale warning badge for stale products', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      // Header stat badge
      expect(screen.getByText(/1 stale price/i)).toBeTruthy();
    });
  });

  it('shows out of stock badge for zero stock products', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/out of stock/i, { exact: false })).toBeTruthy();
    });
  });

  it('shows In Stock badge for products with full stock', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      const okBadges = screen.getAllByText(/✓ In Stock/i);
      expect(okBadges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('opens edit modal when Edit button is clicked', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Corrugated Box/i)).toBeTruthy();
    });
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);
    await waitFor(() => {
      expect(screen.getByText('Edit Product')).toBeTruthy();
      expect(screen.getByText('Save Changes')).toBeTruthy();
    });
  });

  it('closes edit modal when Cancel is clicked', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]);
    });
    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeTruthy();
    });
    fireEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByText('Save Changes')).toBeNull();
    });
  });

  it('opens Add Product modal', async () => {
    render(<PriceListPage />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/\+ Add Product/i));
    });
    await waitFor(() => {
      expect(screen.getByText('Add New Product')).toBeTruthy();
    });
  });

  it('shows error banner when fetch fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));
    render(<PriceListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Could not load products/i)).toBeTruthy();
    });
  });
});
