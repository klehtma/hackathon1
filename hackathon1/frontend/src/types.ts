// Mirrors the backend's ArbOpportunity shape (src/types.ts in the backend repo).
// Keep these two in sync manually, or move to a shared package later.

export interface ArbLeg {
  outcomeName: string;
  bookmaker: string;
  price: number;
  stakePercent: number;
}

export interface ArbOpportunity {
  matchId: string;
  homeTeam: string;
  awayTeam: string;
  commenceTime: string;
  legs: ArbLeg[];
  totalImpliedProbability: number;
  profitPercent: number;
  detectedAt: string;
  sportKey?: string; // optional: include if the backend adds it to the response
}

export interface ArbsResponse {
  arbs: ArbOpportunity[];
  lastUpdated: string;
}
