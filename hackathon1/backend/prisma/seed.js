const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

async function main() {
  await prisma.arbOpportunity.upsert({
    where: { matchId: "demo-match-1" },
    update: {},
    create: {
      matchId: "demo-match-1",
      homeTeam: "Alba Berlin",
      awayTeam: "Bayern Munich",
      commenceTime: new Date(Date.now() + 1000 * 60 * 60 * 24),
      totalImpliedProbability: 0.97,
      profitPercent: 3.09,
      sportKey: "basketball_bundesliga",
      legs: {
        create: [
          { outcomeName: "Alba Berlin", bookmaker: "Coolbet", price: 2.1, stakePercent: 48.5 },
          { outcomeName: "Bayern Munich", bookmaker: "Optibet", price: 2.15, stakePercent: 51.5 },
        ],
      },
    },
  });

  console.log("Seed complete.");
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
