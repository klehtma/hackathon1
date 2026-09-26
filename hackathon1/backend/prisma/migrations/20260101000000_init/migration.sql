-- CreateTable
CREATE TABLE "ArbOpportunity" (
    "id" TEXT NOT NULL,
    "matchId" TEXT NOT NULL,
    "homeTeam" TEXT NOT NULL,
    "awayTeam" TEXT NOT NULL,
    "commenceTime" TIMESTAMP(3) NOT NULL,
    "totalImpliedProbability" DOUBLE PRECISION NOT NULL,
    "profitPercent" DOUBLE PRECISION NOT NULL,
    "detectedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sportKey" TEXT,

    CONSTRAINT "ArbOpportunity_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ArbLeg" (
    "id" TEXT NOT NULL,
    "outcomeName" TEXT NOT NULL,
    "bookmaker" TEXT NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "stakePercent" DOUBLE PRECISION NOT NULL,
    "opportunityId" TEXT NOT NULL,

    CONSTRAINT "ArbLeg_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ArbOpportunity_matchId_key" ON "ArbOpportunity"("matchId");

-- CreateIndex
CREATE INDEX "ArbOpportunity_detectedAt_idx" ON "ArbOpportunity"("detectedAt");

-- AddForeignKey
ALTER TABLE "ArbLeg" ADD CONSTRAINT "ArbLeg_opportunityId_fkey" FOREIGN KEY ("opportunityId") REFERENCES "ArbOpportunity"("id") ON DELETE CASCADE ON UPDATE CASCADE;
