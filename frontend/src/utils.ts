/**
 * Utility functions for the application
 */

/**
 * Format a number as Malaysian Ringgit currency
 * @param amount - The numeric amount to format
 * @param showSign - Whether to show + sign for positive values (default: false)
 * @returns Formatted currency string (e.g., "RM 10.00")
 */
export function formatCurrency(amount: number, showSign = false): string {
  const formatted = `RM ${amount.toFixed(2)}`;
  if (showSign && amount > 0) {
    return `+${formatted}`;
  }
  return formatted;
}

/**
 * Format a number as a discount value
 * @param amount - The discount amount
 * @returns Formatted discount string (e.g., "-RM 5.00")
 */
export function formatDiscount(amount: number): string {
  if (amount <= 0) return '';
  return `-RM ${amount.toFixed(2)}`;
}

export const ORDER_STATUSES = [
  { value: 'Pending Payment', label: 'Pending Payment' },
  { value: 'Payment Under Review', label: 'Payment Under Review' },
  { value: 'Payment Rejected', label: 'Payment Rejected' },
  { value: 'Paid', label: 'Paid' },
  { value: 'Preparing', label: 'Preparing' },
  { value: 'Ready for Pickup', label: 'Ready for Pickup' },
  { value: 'Shipped', label: 'Shipped' },
  { value: 'Completed', label: 'Completed' },
  { value: 'Cancel Requested', label: 'Cancel Requested' },
  { value: 'Cancelled', label: 'Cancelled' },
];
