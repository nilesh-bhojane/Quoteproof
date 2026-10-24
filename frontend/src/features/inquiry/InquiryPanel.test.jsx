import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import InquiryPanel from './InquiryPanel.jsx';

// Mock fetch globally for this test suite
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        items: [
          {
            description: 'Large box',
            quantity: 500,
            unit: 'pcs',
            specifications: {},
            sku: null,
          },
        ],
        missing_fields: ['dimensions/SKU for smaller item'],
        warnings: [],
        mode: 'deterministic_stub_not_llm',
      }),
  })
);

test('runs extraction and displays result', async () => {
  render(<InquiryPanel />);
  const btn = screen.getByRole('button', { name: /run extraction/i });
  fireEvent.click(btn);

  // Loading indicator appears
  expect(screen.getByText(/extracting/i)).toBeInTheDocument();

  // Wait for result to appear
  await waitFor(() => expect(screen.getByText(/large box/i)).toBeInTheDocument());
  expect(screen.getByText(/500 pcs/i)).toBeInTheDocument();
  expect(screen.getByText(/missing details/i)).toBeInTheDocument();
});
