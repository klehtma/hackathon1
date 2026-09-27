# Hackathon

A small full-stack app (Node.js backend + frontend + PostgreSQL), containerized with Docker and deployed on AWS EC2.

**Live demo:** https://arbetter.duckdns.org/ 
- requires user/password

## Stack
- Backend: Node.js
- Database: PostgreSQL 17
- Frontend: static/JS, served via Docker
- Deployment: Docker Compose on EC2, auto-deployed via GitHub Actions on push to `main`

## Running locally
\`\`\`bash
cp .env.example .env   # fill in your secrets
docker compose up -d --build
\`\`\`

Then visit `http://localhost:8080`.

## Deployment
Pushing to `main` triggers `.github/workflows/deploy.yml`, which SSHes into the EC2 instance, pulls the latest code, and rebuilds the containers.
