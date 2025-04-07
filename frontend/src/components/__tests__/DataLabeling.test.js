import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DataLabeling from '../DataLabeling';
import { getEvents } from '../../services/api';

// Мокаємо модуль API
jest.mock('../../services/api', () => ({
  getEvents: jest.fn(),
  getEvent: jest.fn(),
  labelEvent: jest.fn()
}));

describe('DataLabeling Component', () => {
  beforeEach(() => {
    // Налаштовуємо мок-відповідь
    getEvents.mockResolvedValue({
      data: {
        events: [
          {
            id: 1,
            event_id: 'event-001',
            severity: 'high',
            source_ip: '192.168.1.1',
            timestamp: '2023-01-01T12:00:00Z',
            manual_review: false,
            manual_tags: [],
            event_data: {}
          }
        ],
        page: 1,
        page_size: 10,
        total_count: 1,
        total_pages: 1
      }
    });
  });

  test('renders without crashing', async () => {
    render(<DataLabeling />);
    expect(screen.getByText(/Data Labeling/i)).toBeInTheDocument();
    await waitFor(() => expect(getEvents).toHaveBeenCalled());
  });

  test('displays events when loaded', async () => {
    render(<DataLabeling />);
    await waitFor(() => expect(screen.getByText('192.168.1.1')).toBeInTheDocument());
  });

  // Додаткові тести
  test('applies filters correctly', async () => {
    render(<DataLabeling />);
    
    // Wait for initial load
    await waitFor(() => expect(screen.getByText('192.168.1.1')).toBeInTheDocument());
    
    // Set up mock for filtered results
    getEvents.mockResolvedValueOnce({
      data: {
        events: [
          {
            id: 2,
            event_id: 'event-002',
            severity: 'critical',
            source_ip: '10.0.0.1',
            timestamp: '2023-01-02T12:00:00Z',
            manual_review: false,
            manual_tags: [],
            event_data: {}
          }
        ],
        page: 1,
        page_size: 10,
        total_count: 1,
        total_pages: 1
      }
    });
    
    // Select severity filter
    const severitySelect = screen.getByLabelText(/Severity:/i);
    fireEvent.change(severitySelect, { target: { value: 'critical' } });
    
    // Click apply filters
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);
    
    // Check that filtered results are displayed
    await waitFor(() => {
      expect(screen.getByText('10.0.0.1')).toBeInTheDocument();
      expect(getEvents).toHaveBeenCalledWith(expect.objectContaining({
        severity: 'critical'
      }));
    });
  });
});
