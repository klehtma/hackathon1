const { PrismaClient } = require("@prisma/client");

// Reuse a single PrismaClient instance (avoids exhausting Postgres
// connections when the module is reloaded, e.g. with --watch in dev).
const globalForPrisma = globalThis;

const prisma =
  globalForPrisma.__prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "production" ? ["error", "warn"] : ["query", "error", "warn"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.__prisma = prisma;
}

module.exports = { prisma };
