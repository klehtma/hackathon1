interface FilterSidebarProps {
  minProfit: number;
  onMinProfitChange: (value: number) => void;
  sportFilter: string;
  onSportFilterChange: (value: string) => void;
  availableSports: string[];
}

export default function FilterSidebar({
  minProfit,
  onMinProfitChange,
  sportFilter,
  onSportFilterChange,
  availableSports,
}: FilterSidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar__section">
        <label className="sidebar__label" htmlFor="min-profit">
          Minimum profit
        </label>
        <div className="sidebar__profit-input">
          <input
            id="min-profit"
            type="number"
            step="0.1"
            min="0"
            value={minProfit}
            onChange={(e) => onMinProfitChange(Number(e.target.value))}
          />
          <span>%</span>
        </div>
      </div>

      <div className="sidebar__section">
        <label className="sidebar__label" htmlFor="sport-filter">
          Sport
        </label>
        <select
          id="sport-filter"
          value={sportFilter}
          onChange={(e) => onSportFilterChange(e.target.value)}
        >
          <option value="all">All sports</option>
          {availableSports.map((sport) => (
            <option key={sport} value={sport}>
              {sport}
            </option>
          ))}
        </select>
      </div>

      <div className="sidebar__note">
        Opportunities are ranked by profit %, highest first. Rows fade as
        they age — a stale row means the odds have likely moved since
        detection.
      </div>
    </aside>
  );
}
