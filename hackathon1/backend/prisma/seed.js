const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

// Mock arbitrage opportunities, standing in for what data_service will
// eventually produce by crawling Coolbet / Epicbet / Optibet.
// - commenceTime: mix of near-future matches
// - detectedAt: staggered into the past so the frontend's "stale row" fade
//   (see FilterSidebar's note) actually has something to show
// - profitPercent: spans both sides of the frontend's default 1.0% filter
//   so the min-profit slider visibly does something out of the box
const hoursFromNow = (h) => new Date(Date.now() + h * 60 * 60 * 1000);
const minutesAgo = (m) => new Date(Date.now() - m * 60 * 1000);

const opportunities = [
  {
    matchId: "demo-match-1",
    homeTeam: "Alba Berlin",
    awayTeam: "Bayern Munich",
    commenceTime: hoursFromNow(24),
    sportKey: "basketball_bundesliga",
    totalImpliedProbability: 0.97,
    profitPercent: 3.09,
    detectedAt: minutesAgo(2),
    legs: [
      { outcomeName: "Alba Berlin", bookmaker: "Coolbet", price: 2.1, stakePercent: 48.5 },
      { outcomeName: "Bayern Munich", bookmaker: "Optibet", price: 2.15, stakePercent: 51.5 },
    ],
  },
  {
    matchId: "demo-match-2",
    homeTeam: "Levadia Tallinn",
    awayTeam: "Flora Tallinn",
    commenceTime: hoursFromNow(6),
    sportKey: "soccer_estonia_meistriliiga",
    totalImpliedProbability: 0.9412,
    profitPercent: 5.88,
    detectedAt: minutesAgo(5),
    legs: [
      { outcomeName: "Levadia Tallinn", bookmaker: "Optibet", price: 2.5, stakePercent: 33.9 },
      { outcomeName: "Draw", bookmaker: "Coolbet", price: 3.4, stakePercent: 24.9 },
      { outcomeName: "Flora Tallinn", bookmaker: "Epicbet", price: 3.6, stakePercent: 23.5 },
    ],
  },
  {
    matchId: "demo-match-3",
    homeTeam: "Real Madrid",
    awayTeam: "Manchester City",
    commenceTime: hoursFromNow(30),
    sportKey: "soccer_uefa_champs_league",
    totalImpliedProbability: 0.9856,
    profitPercent: 1.46,
    detectedAt: minutesAgo(11),
    legs: [
      { outcomeName: "Real Madrid", bookmaker: "Epicbet", price: 2.4, stakePercent: 39.8 },
      { outcomeName: "Draw", bookmaker: "Coolbet", price: 3.5, stakePercent: 27.3 },
      { outcomeName: "Manchester City", bookmaker: "Optibet", price: 3.05, stakePercent: 31.4 },
    ],
  },
  {
    matchId: "demo-match-4",
    homeTeam: "Novak Djokovic",
    awayTeam: "Carlos Alcaraz",
    commenceTime: hoursFromNow(18),
    sportKey: "tennis_atp",
    totalImpliedProbability: 0.9921,
    profitPercent: 0.79,
    detectedAt: minutesAgo(18),
    legs: [
      { outcomeName: "Novak Djokovic", bookmaker: "Coolbet", price: 1.95, stakePercent: 50.8 },
      { outcomeName: "Carlos Alcaraz", bookmaker: "Epicbet", price: 2.05, stakePercent: 49.2 },
    ],
  },
  {
    matchId: "demo-match-5",
    homeTeam: "Toronto Maple Leafs",
    awayTeam: "Boston Bruins",
    commenceTime: hoursFromNow(9),
    sportKey: "icehockey_nhl",
    totalImpliedProbability: 0.9683,
    profitPercent: 3.27,
    detectedAt: minutesAgo(3),
    legs: [
      { outcomeName: "Toronto Maple Leafs", bookmaker: "Optibet", price: 2.2, stakePercent: 46.4 },
      { outcomeName: "Boston Bruins", bookmaker: "Coolbet", price: 1.85, stakePercent: 53.6 },
    ],
  },
  {
    matchId: "demo-match-6",
    homeTeam: "Los Angeles Lakers",
    awayTeam: "Boston Celtics",
    commenceTime: hoursFromNow(14),
    sportKey: "basketball_nba",
    totalImpliedProbability: 0.9998,
    profitPercent: 0.24,
    detectedAt: minutesAgo(42),
    legs: [
      { outcomeName: "Los Angeles Lakers", bookmaker: "Epicbet", price: 1.91, stakePercent: 51.3 },
      { outcomeName: "Boston Celtics", bookmaker: "Optibet", price: 2.0, stakePercent: 48.7 },
    ],
  },
  {
    matchId: "demo-match-7",
    homeTeam: "Paris Saint-Germain",
    awayTeam: "Borussia Dortmund",
    commenceTime: hoursFromNow(48),
    sportKey: "soccer_uefa_champs_league",
    totalImpliedProbability: 0.9539,
    profitPercent: 4.61,
    detectedAt: minutesAgo(7),
    legs: [
      { outcomeName: "Paris Saint-Germain", bookmaker: "Coolbet", price: 1.65, stakePercent: 55.6 },
      { outcomeName: "Draw", bookmaker: "Optibet", price: 4.2, stakePercent: 21.8 },
      { outcomeName: "Borussia Dortmund", bookmaker: "Epicbet", price: 4.6, stakePercent: 19.9 },
    ],
  },
  {
    matchId: "demo-match-8",
    homeTeam: "Iga Swiatek",
    awayTeam: "Aryna Sabalenka",
    commenceTime: hoursFromNow(3),
    sportKey: "tennis_wta",
    totalImpliedProbability: 0.9994,
    profitPercent: 0.06,
    detectedAt: minutesAgo(55),
    legs: [
      { outcomeName: "Iga Swiatek", bookmaker: "Coolbet", price: 1.72, stakePercent: 58.1 },
      { outcomeName: "Aryna Sabalenka", bookmaker: "Epicbet", price: 2.4, stakePercent: 41.9 },
    ],
  },
  {
    matchId: "demo-match-9",
    homeTeam: "New York Yankees",
    awayTeam: "Boston Red Sox",
    commenceTime: hoursFromNow(20),
    sportKey: "baseball_mlb",
    totalImpliedProbability: 0.9701,
    profitPercent: 3.08,
    detectedAt: minutesAgo(9),
    legs: [
      { outcomeName: "New York Yankees", bookmaker: "Optibet", price: 1.8, stakePercent: 56.9 },
      { outcomeName: "Boston Red Sox", bookmaker: "Coolbet", price: 2.35, stakePercent: 43.1 },
    ],
  },
  {
    matchId: "demo-match-10",
    homeTeam: "Pari Nizhny Novgorod",
    awayTeam: "Zenit St. Petersburg",
    commenceTime: hoursFromNow(11),
    sportKey: "soccer_russia_premier_league",
    totalImpliedProbability: 0.9327,
    profitPercent: 6.73,
    detectedAt: minutesAgo(14),
    legs: [
      { outcomeName: "Pari Nizhny Novgorod", bookmaker: "Epicbet", price: 4.1, stakePercent: 24.6 },
      { outcomeName: "Draw", bookmaker: "Coolbet", price: 3.3, stakePercent: 30.5 },
      { outcomeName: "Zenit St. Petersburg", bookmaker: "Optibet", price: 2.1, stakePercent: 44.9 },
    ],
  },
];

async function main() {
  for (const { legs, ...opportunity } of opportunities) {
    await prisma.arbOpportunity.upsert({
      where: { matchId: opportunity.matchId },
      update: {
        ...opportunity,
        legs: {
          deleteMany: {},
          create: legs,
        },
      },
      create: {
        ...opportunity,
        legs: { create: legs },
      },
    });
  }

  console.log(`Seed complete. Upserted ${opportunities.length} arb opportunities.`);
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });