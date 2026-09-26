# arb-finder-frontend

A live dashboard showing detected arbitrage opportunities, polled from the
backend every 10 seconds. Filterable by sport and minimum profit %, with
per-match stake breakdowns.

## API contract (share this with your backend partner)

This expects a single endpoint:

```
GET /api/arbs

Response 200:
{
  "arbs": [
    {
      "matchId": "string",
      "homeTeam": "string",
      "awayTeam": "string",
      "commenceTime": "ISO 8601 string",
      "sportKey": "string (optional)",
      "legs": [
        { "outcomeName": "string", "bookmaker": "string", "price": number, "stakePercent": number }
      ],
      "totalImpliedProbability": number,
      "profitPercent": number,
      "detectedAt": "ISO 8601 string"
    }
  ],
  "lastUpdated": "ISO 8601 string"
}
```

This lines up with the `ArbOpportunity` type in the backend's
`arbCalculator.ts` — if the backend project structure matches the one from
earlier in this project, this endpoint just needs to wrap `findAllArbs()`'s
output in `{ arbs, lastUpdated }` and expose it over HTTP (e.g. a small
Express route), plus enable CORS for the frontend's origin.

## Local development

1. `npm install`
2. Copy `.env.example` to `.env` and point `VITE_API_BASE_URL` at your
   backend (e.g. `http://localhost:3000` while your partner runs it locally,
   or your EC2 instance's address once deployed).
3. `npm run dev`

## Deploying the frontend to AWS

The fastest path for a hackathon is **AWS Amplify Hosting** — it builds and
deploys straight from your GitHub repo with no manual S3/CloudFront setup:

1. Push this frontend to a GitHub repo (can be a subfolder of your monorepo,
   or its own repo).
2. In the AWS Console, go to **AWS Amplify → Host a web app**.
3. Connect your GitHub account and pick the repo/branch. If it's a subfolder
   in a monorepo, set the "app root" to that subfolder in the build settings.
4. Amplify auto-detects Vite; confirm the build settings look like:
   ```
   build:
     commands:
       - npm install
       - npm run build
   artifacts:
     baseDirectory: dist
     files:
       - '**/*'
   ```
5. Add `VITE_API_BASE_URL` as an environment variable in Amplify's app
   settings, pointing at your backend's real address (your EC2 instance's
   public IP/domain and port, or an API Gateway URL if your partner sets
   that up).
6. Save and deploy — Amplify gives you a live HTTPS URL, and every push to
   the connected branch auto-redeploys.

**Why Amplify over manually configuring S3 + CloudFront:** it's one flow
instead of separately creating a bucket, setting a bucket policy, setting up
a CloudFront distribution, and wiring an origin — Amplify handles all of
that for you, which matters a lot when you're on a hackathon clock. If you
have more time later, S3 + CloudFront gives more fine-grained control, but
isn't necessary for getting this live and demoable.

**One thing to sort out with your partner:** if the backend EC2 instance
only allows inbound SSH (per the earlier AWS setup), you'll need to also
open the port your backend's API listens on (e.g. 3000) in its security
group, restricted appropriately — otherwise this frontend can't reach it
from the browser.
