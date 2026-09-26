import { ArbsResponse } from "./types";

// Set VITE_API_BASE_URL in .env to your backend's URL, e.g.
// http://localhost:3000 for local dev, or your EC2/API Gateway URL in production.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

/**
 * Expects the backend to expose GET /api/arbs returning:
 *   { arbs: ArbOpportunity[], lastUpdated: string }
 * This is the one contract your backend partner needs to match — confirm
 * the shape with them before wiring this up for real.
 */
export async function fetchArbs(): Promise<ArbsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/arbs`);
  if (!response.ok) {
    throw new Error(`Backend error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
