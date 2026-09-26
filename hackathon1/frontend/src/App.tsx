import { useEffect, useState, useMemo, useCallback } from "react";
import StatusBar from "./components/StatusBar";
import FilterSidebar from "./components/FilterSidebar";
import ArbTable from "./components/ArbTable";
import { fetchArbs } from "./api";
import { ArbOpportunity } from "./types";

const POLL_INTERVAL_MS = 10_000;

export default function App() {
  const [arbs, setArbs] = useState<ArbOpportunity[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [minProfit, setMinProfit] = useState(1.0);
  const [sportFilter, setSportFilter] = useState("all");

  const poll = useCallback(async () => {
    try {
      const data = await fetchArbs();
      setArbs(data.arbs);
      setLastUpdated(data.lastUpdated);
      setIsConnected(true);
    } catch (err) {
      console.error("Failed to fetch arbs:", err);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [poll]);

  const availableSports = useMemo(() => {
    const sports = new Set<string>();
    arbs.forEach((a) => a.sportKey && sports.add(a.sportKey));
    return Array.from(sports).sort();
  }, [arbs]);

  const filteredArbs = useMemo(() => {
    return arbs
      .filter((a) => a.profitPercent >= minProfit)
      .filter((a) => sportFilter === "all" || a.sportKey === sportFilter)
      .sort((a, b) => b.profitPercent - a.profitPercent);
  }, [arbs, minProfit, sportFilter]);

  return (
    <div className="app">
      <StatusBar
        isConnected={isConnected}
        lastUpdated={lastUpdated}
        arbCount={filteredArbs.length}
      />
      <div className="app__body">
        <FilterSidebar
          minProfit={minProfit}
          onMinProfitChange={setMinProfit}
          sportFilter={sportFilter}
          onSportFilterChange={setSportFilter}
          availableSports={availableSports}
        />
        <main className="app__main">
          <ArbTable arbs={filteredArbs} />
        </main>
      </div>
    </div>
  );
}
