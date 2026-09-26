import { ArbOpportunity } from "../types";
import ArbRow from "./ArbRow";

interface ArbTableProps {
  arbs: ArbOpportunity[];
}

export default function ArbTable({ arbs }: ArbTableProps) {
  if (arbs.length === 0) {
    return (
      <div className="empty-state">
        <p>No arbs matching your filters right now.</p>
        <p className="empty-state__sub">
          The board refreshes automatically — lower your minimum profit
          threshold or widen the sport filter to see more.
        </p>
      </div>
    );
  }

  return (
    <div className="arb-table">
      <div className="arb-table__header">
        <span>Match</span>
        <span>Kickoff</span>
        <span>Books</span>
        <span className="align-right">Profit</span>
        <span />
      </div>
      <div className="arb-table__body">
        {arbs.map((arb) => (
          <ArbRow key={`${arb.matchId}-${arb.detectedAt}`} arb={arb} />
        ))}
      </div>
    </div>
  );
}
