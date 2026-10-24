import { render, screen, fireEvent } from '@testing-library/react';
import { test, expect } from 'vitest';
import AnalyticsPanel from './AnalyticsPanel.jsx';

test('renders analytics panel and metrics heading', () => {
  render(<AnalyticsPanel />);
  expect(screen.getByText(/productivity evidence/i)).toBeInTheDocument();
});

test('calculates time saved and percentage reduction based on duration inputs', () => {
  render(<AnalyticsPanel />);
  // Default: manual 10 min, assisted 4 min -> 6.0 min saved, 60.0% reduction
  expect(screen.getByText(/6.0 min/)).toBeInTheDocument();
  expect(screen.getByText(/60.0%/)).toBeInTheDocument();
});

test('does not calculate labour value without explicit hourly cost', () => {
  render(<AnalyticsPanel />);
  // Explicit rule: without hourly cost, shows dash '—'
  expect(screen.getByText('—')).toBeInTheDocument();
});

test('calculates labour value when explicit hourly rate is entered', () => {
  render(<AnalyticsPanel />);
  const hourlyInput = screen.getByPlaceholderText(/optional explicit rate/i);
  fireEvent.change(hourlyInput, { target: { value: '600' } });
  // 6 minutes saved = 0.1 hours * ₹600 = ₹60.00
  expect(screen.getByText(/₹60.00/)).toBeInTheDocument();
});
