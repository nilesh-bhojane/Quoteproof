import { render, screen, fireEvent } from '@testing-library/react';
import QuotationPanel from './QuotationPanel.jsx';

// ---------------------------------------------------------------------------
// QuotationPanel — Contributor B tests
// ---------------------------------------------------------------------------

// Mock the JSON import used by the component
jest.mock('../data/priceList.json', () => [
  { sku: 'DEMO001', description: 'Large box', unitPrice: 24 },
  { sku: 'SMALL001', description: 'Small box', unitPrice: 12 },
]);

test('renders quotation review heading', () => {
  render(<QuotationPanel />);
  expect(screen.getByText(/quotation review/i)).toBeInTheDocument();
});

test('shows validation warning when items have zero quantity', () => {
  render(<QuotationPanel />);
  // Small box starts with qty 0, so a warning should be visible
  expect(screen.getByText(/validation warning/i)).toBeInTheDocument();
});

test('approve button is disabled when fields are unresolved', () => {
  render(<QuotationPanel />);
  const approveBtn = screen.getByRole('button', { name: /approve/i });
  expect(approveBtn).toBeDisabled();
});

test('calculates subtotal correctly for rendered items', () => {
  render(<QuotationPanel />);
  // Large box: 500 * 24 = 12,000
  // The ₹12,000.00 total should appear somewhere as a line total
  expect(screen.getByText(/12,000/)).toBeInTheDocument();
});

test('reject button is always available', () => {
  render(<QuotationPanel />);
  const rejectBtn = screen.getByRole('button', { name: /reject/i });
  expect(rejectBtn).not.toBeDisabled();
});

test('editing quantity resets status to draft', () => {
  render(<QuotationPanel />);
  const qtyInputs = screen.getAllByLabelText(/quantity/i);
  fireEvent.change(qtyInputs[0], { target: { value: '100' } });
  expect(screen.getByText(/awaiting review/i)).toBeInTheDocument();
});
