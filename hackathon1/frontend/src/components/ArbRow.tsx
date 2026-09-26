import { useState } from "react";
import { ArbOpportunity } from "../types";

interface ArbRowProps {
  arb: ArbOpportunity;
}

export default function ArbRow({ arb }: ArbRowProps) {
  const [expanded, setExpanded] = useState(false);
  const ageSeconds = Math.floor((Date.now() - new Date(arb.detectedAt).getTime()) / 1000);
  const isStale = ageSeconds > 90; // arbs this old are likely already gone

  return (
    <div className={`arb-row ${isStale ? "arb-row--stale" : ""}`}>
      <button
        className="arb-row__summary"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="arb-row__matchup">
          {arb.homeTeam} <span className="arb-row__vs">vs</span> {arb.awayTeam}
        </span>
        <span className="arb-row__kickoff">{formatKickoff(arb.commenceTime)}</span>
        <span className="arb-row__books">
          {arb.legs.map((l) => l.bookmaker).join(" · ")}
        </span>
        <span className="arb-row__profit">{arb.profitPercent.toFixed(2)}%</span>
        <span className={`arb-row__caret ${expanded ? "is-open" : ""}`}>▾</span>
      </button>

      {expanded && (
        <div className="arb-row__detail">
          <table className="arb-row__legs">
            <thead>
              <tr>
                <th>Outcome</th>
                <th>Bookmaker</th>
                <th>Odds</th>
                <th>Stake split</th>
              </tr>
            </thead>
            <tbody>
              {arb.legs.map((leg, i) => (
                <tr key={i}>
                  <td>{leg.outcomeName}</td>
                  <td>{leg.bookmaker}</td>
                  <td className="num">{leg.price.toFixed(2)}</td>
                  <td className="num">{leg.stakePercent.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="arb-row__footnote">
            Detected {ageSeconds}s ago · implied probability{" "}
            {(arb.totalImpliedProbability * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  );
}

function formatKickoff(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
