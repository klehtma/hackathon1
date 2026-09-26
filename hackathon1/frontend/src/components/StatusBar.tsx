interface StatusBarProps {
  isConnected: boolean;
  lastUpdated: string | null;
  arbCount: number;
}

export default function StatusBar({ isConnected, lastUpdated, arbCount }: StatusBarProps) {
  return (
    <header className="status-bar">
      <div className="status-bar__brand">
        <span className="status-bar__mark">ARB/FINDER</span>
      </div>
      <div className="status-bar__meta">
        <span className={`status-bar__dot ${isConnected ? "is-live" : "is-down"}`} />
        <span className="status-bar__label">
          {isConnected ? "Live" : "Disconnected"}
        </span>
        <span className="status-bar__divider" />
        <span className="status-bar__count">{arbCount} open</span>
        <span className="status-bar__divider" />
        <span className="status-bar__updated">
          {lastUpdated ? `Updated ${formatTime(lastUpdated)}` : "Waiting for data…"}
        </span>
      </div>
    </header>
  );
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
