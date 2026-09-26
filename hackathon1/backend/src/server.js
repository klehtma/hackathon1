const express = require("express");
const cors = require("cors");
const { prisma } = require("./db");

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.use(cors());
app.use(express.json());

// Used by docker-compose's healthcheck (and an AWS load balancer / target
// group health check, if you add one later).
app.get("/health", (_req, res) => {
  res.status(200).json({ status: "ok" });
});

// Contract the frontend expects (frontend/src/api.ts):
//   GET /api/arbs -> { arbs: ArbOpportunity[], lastUpdated: string }
app.get("/api/arbs", async (_req, res) => {
  try {
    const opportunities = await prisma.arbOpportunity.findMany({
      include: { legs: true },
      orderBy: { detectedAt: "desc" },
      take: 100,
    });

    const arbs = opportunities.map((o) => ({
      matchId: o.matchId,
      homeTeam: o.homeTeam,
      awayTeam: o.awayTeam,
      commenceTime: o.commenceTime.toISOString(),
      legs: o.legs.map((leg) => ({
        outcomeName: leg.outcomeName,
        bookmaker: leg.bookmaker,
        price: leg.price,
        stakePercent: leg.stakePercent,
      })),
      totalImpliedProbability: o.totalImpliedProbability,
      profitPercent: o.profitPercent,
      detectedAt: o.detectedAt.toISOString(),
      ...(o.sportKey ? { sportKey: o.sportKey } : {}),
    }));

    res.status(200).json({
      arbs,
      lastUpdated: new Date().toISOString(),
    });
  } catch (err) {
    console.error("GET /api/arbs failed:", err);
    res.status(500).json({ error: "Failed to load arb opportunities" });
  }
});

app.use((_req, res) => {
  res.status(404).json({ error: "Not found" });
});

const server = app.listen(PORT, () => {
  console.log(`Backend listening on port ${PORT} (${process.env.NODE_ENV ?? "development"})`);
});

// Graceful shutdown so `docker stop` / ECS deployments don't hang.
for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, async () => {
    console.log(`${signal} received, shutting down`);
    server.close(() => console.log("HTTP server closed"));
    await prisma.$disconnect();
    process.exit(0);
  });
}
