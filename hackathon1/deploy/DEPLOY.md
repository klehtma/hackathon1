# Deploying to AWS (single EC2 instance)

This stack (Postgres + backend + frontend, and eventually data_service) is
built for one always-on host running `docker compose`, not for splitting
across Lambda/Fargate — mainly because of `data_service`'s browser
automation and local LLM, which want persistent memory/CPU rather than
serverless. A single EC2 instance is the simplest thing that matches what
you already have.

## 1. Launch the instance

- AMI: **Ubuntu Server 24.04 LTS**
- Instance type: **t3.small** to start (2 vCPU / 2GB) — bump to `t3.medium`
  once `data_service` (browser + LLM) is added, they're memory-hungry.
- Storage: 20-30 GB gp3 (container images + Postgres data + browser binaries
  add up).
- Key pair: create/select one you have the private key for.
- Network: create or reuse a **Security Group** allowing:
  | Type  | Port | Source          | Why                     |
  |-------|------|------------------|--------------------------|
  | SSH   | 22   | your IP only     | admin access             |
  | HTTP  | 80   | 0.0.0.0/0        | the app                  |
  | HTTPS | 443  | 0.0.0.0/0        | once you add TLS (below) |

  Don't open 3000 (backend) or 5432 (postgres) publicly — the frontend's
  nginx proxies to the backend over the private Docker network, and
  Postgres should never be internet-facing.
- Allocate and associate an **Elastic IP** so the address doesn't change on
  reboot.

## 2. Copy the project up and install Docker

```bash
scp -i your-key.pem -r hackathon1 ubuntu@<ELASTIC_IP>:~/
ssh -i your-key.pem ubuntu@<ELASTIC_IP>
cd hackathon1
chmod +x deploy/ec2-setup.sh
./deploy/ec2-setup.sh
# log out and back in so the docker group membership takes effect
exit
ssh -i your-key.pem ubuntu@<ELASTIC_IP>
```

## 3. Configure secrets

```bash
cd hackathon1
cp .env.example .env
nano .env   # fill in real passwords — don't use the example ones
```

## 4. Build and run

```bash
docker compose up -d --build
docker compose ps          # everything should show "healthy" after ~30s
docker compose logs -f backend
```

The first boot runs the Postgres init script (creates the `backend` /
`data_service` DB roles) and the backend's `prisma migrate deploy`
automatically — no manual DB setup needed.

To load a demo record so `/api/arbs` returns something before
`data_service` is producing real data:

```bash
docker compose exec backend node prisma/seed.js
```

Visit `http://<ELASTIC_IP>` — you should see the frontend, pulling live
from `/api/arbs`.

## 5. (Optional) put a domain + HTTPS in front of it

Point an A record at the Elastic IP, then run Caddy or certbot on the host
in front of the `frontend` container — the simplest is swapping in Caddy as
a second reverse proxy on 80/443 that forwards to the frontend container on
8080 and handles Let's Encrypt automatically. Ask if you want this wired
into the compose file.

## 6. Redeploying after code changes

```bash
git pull   # or scp the updated files up again
docker compose up -d --build
```

## Notes / things left out on purpose

- **`data_service` isn't containerized yet.** It uses Camoufox (a
  stealth browser) and a local Ollama LLM — both want real testing/tuning
  in a container, and the script itself currently exits partway through
  (see the `exit()` in `main.py`). Worth doing as its own step once you've
  decided it's ready. Also worth being aware: it scrapes odds from
  betting-site pages using anti-bot-detection tooling, which likely runs
  against those sites' terms of service — that's a call for you to make,
  not a blocker I've enforced here.
- Backups: `postgres_data` is a named Docker volume on the instance's own
  disk — if the instance is terminated without snapshotting the volume,
  the data's gone. For anything beyond a demo, consider RDS instead of the
  in-container Postgres, or at least periodic `pg_dump` to S3.
