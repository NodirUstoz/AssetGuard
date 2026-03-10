/**
 * Form validation utilities used with react-hook-form.
 */

/**
 * Validate that a string is not empty or whitespace-only.
 */
export function required(value: string): string | true {
  if (!value || !value.trim()) return "This field is required.";
  return true;
}

/**
 * Validate email format.
 */
export function isValidEmail(value: string): string | true {
  if (!value) return true; // Let 'required' handle emptiness
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!pattern.test(value)) return "Please enter a valid email address.";
  return true;
}

/**
 * Validate that a value is a positive number.
 */
export function isPositiveNumber(value: string | number): string | true {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num) || num < 0) return "Must be a non-negative number.";
  return true;
}

/**
 * Validate MAC address format (e.g., AA:BB:CC:DD:EE:FF).
 */
export function isValidMacAddress(value: string): string | true {
  if (!value) return true;
  const pattern = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/;
  if (!pattern.test(value)) return "Invalid MAC address format (expected AA:BB:CC:DD:EE:FF).";
  return true;
}

/**
 * Validate IP address (both v4 and v6 allowed, basic check).
 */
export function isValidIpAddress(value: string): string | true {
  if (!value) return true;
  // Simple IPv4 check
  const ipv4 = /^(\d{1,3}\.){3}\d{1,3}$/;
  // Simple IPv6 check (allows :: shorthand)
  const ipv6 = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
  if (!ipv4.test(value) && !ipv6.test(value)) {
    return "Invalid IP address format.";
  }
  if (ipv4.test(value)) {
    const parts = value.split(".").map(Number);
    if (parts.some((p) => p > 255)) return "Invalid IPv4 address.";
  }
  return true;
}

/**
 * Validate password strength.
 */
export function isStrongPassword(value: string): string | true {
  if (!value) return true;
  if (value.length < 10) return "Password must be at least 10 characters.";
  if (!/[A-Z]/.test(value)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(value)) return "Password must contain at least one lowercase letter.";
  if (!/[0-9]/.test(value)) return "Password must contain at least one digit.";
  return true;
}

/**
 * Create a max-length validator.
 */
export function maxLength(max: number) {
  return (value: string): string | true => {
    if (!value) return true;
    if (value.length > max) return `Must be ${max} characters or fewer.`;
    return true;
  };
}

/**
 * Validate asset tag format: alphanumeric + hyphens, 3-50 characters.
 */
export function isValidAssetTag(value: string): string | true {
  if (!value) return "Asset tag is required.";
  const pattern = /^[A-Za-z0-9\-]{3,50}$/;
  if (!pattern.test(value)) {
    return "Asset tag must be 3-50 characters, using only letters, numbers, and hyphens.";
  }
  return true;
}
