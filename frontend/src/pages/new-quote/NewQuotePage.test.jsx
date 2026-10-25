import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import NewQuotePage from './NewQuotePage.jsx';

// Mock fetch for /api/v1/quotes/draft
const MOCK_DRAFT = {
  id: 'test-quote-uuid',
  status: 'draft',
  inquiry_masked: 'Need [QTY] pcs box.',
  items: [
    {
      id: 'item-1',
      description: 'Corrugated Box 12x10x8 (3-Ply)',
      qty: '100',
      unit: 'pcs',
      unit_price_snapshot: '24.00',
      line_total: '2400.00',
      stock_status: 'ok',
      flags: [],
      explain_text: 'Standard rate ₹24.00/pcs. Bulk tier applies at 500+ pcs.',
      decision_required: false,
      available_stock: 5000,
    },
  ],
  subtotal: '2400.00',
  gst_rate_pct: '18.00',
  gst: '432.00',
  total: '2832.00',
  blocking_flags: [],
  warning_flags: [],
  can_approve: true,
  mode_used: 'basic',
  tokens_in: 0,
  tokens_out: 0,
  cost_inr: '0.00',
};

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(MOCK_DRAFT),
  });
});

describe('NewQuotePage', () => {
  it('renders inquiry input and check button', () => {
    render(<NewQuotePage />);
    expect(screen.getByPlaceholderText(/paste the customer/i)).toBeTruthy();
    expect(screen.getByText(/Check & Draft Quote/i)).toBeTruthy();
  });

  it('shows error when inquiry is empty and draft is clicked', async () => {
    render(<NewQuotePage />);
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));
    await waitFor(() => {
      expect(screen.getByText(/please enter or paste/i)).toBeTruthy();
    });
  });

  it('calls /api/v1/quotes/draft with basic mode and renders draft table', async () => {
    render(<NewQuotePage />);

    // Type custom inquiry
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need 100 boxes 12x10x8' } });

    // Enable basic mode
    fireEvent.click(screen.getByRole('checkbox'));

    // Click draft button
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/quotes/draft',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    // Draft table should render item
    await waitFor(() => {
      expect(screen.getAllByText(/Corrugated Box 12x10x8/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows In Stock badge for ok stock status', async () => {
    render(<NewQuotePage />);
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need 100 boxes 12x10x8' } });
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));
    await waitFor(() => {
      expect(screen.getByText(/✓ In Stock/i)).toBeTruthy();
    });
  });

  it('shows approval ready banner when can_approve is true', async () => {
    render(<NewQuotePage />);
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need 100 boxes 12x10x8' } });
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));
    await waitFor(() => {
      expect(screen.getByText(/ready for approval/i)).toBeTruthy();
    });
  });

  it('shows blocking banner when blocking flags present', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ...MOCK_DRAFT,
          blocking_flags: [
            {
              code: 'MISSING_QUANTITY',
              severity: 'blocking',
              message: 'Quantity is missing for item.',
              blocks_approval: true,
            },
          ],
          can_approve: false,
        }),
    });

    render(<NewQuotePage />);
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need some boxes' } });
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));
    await waitFor(() => {
      expect(screen.getByText(/blocking flag/i)).toBeTruthy();
    });
  });

  it('renders short-stock decision panel for shortage items', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          ...MOCK_DRAFT,
          items: [
            {
              ...MOCK_DRAFT.items[0],
              stock_status: 'short',
              decision_required: true,
              available_stock: 120,
              qty: '500',
              copyable_reply: null,
            },
          ],
          blocking_flags: [
            {
              code: 'STOCK_SHORT',
              severity: 'blocking',
              message: 'Only 120 available.',
              blocks_approval: true,
            },
          ],
          can_approve: false,
        }),
    });

    render(<NewQuotePage />);
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need 500 boxes' } });
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));

    await waitFor(() => {
      expect(screen.getAllByText(/Only.*available/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Quote.*now/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Apply Decision/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('calls onSendToReview when Send to Review is clicked', async () => {
    const mockSend = vi.fn();
    render(<NewQuotePage onSendToReview={mockSend} />);
    const textarea = screen.getByPlaceholderText(/paste the customer/i);
    fireEvent.change(textarea, { target: { value: 'Need 100 boxes 12x10x8' } });
    fireEvent.click(screen.getByText(/Check & Draft Quote/i));

    await waitFor(() => {
      expect(screen.getByText(/Send to Review/i)).toBeTruthy();
    });
    fireEvent.click(screen.getByText(/Send to Review/i));
    expect(mockSend).toHaveBeenCalledWith(MOCK_DRAFT);
  });
});
