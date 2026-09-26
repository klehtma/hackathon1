#!/bin/bash
# Run this ONCE on a fresh EC2 instance (Ubuntu 24.04 LTS) to install
# Docker + the Compose plugin. Usage:
#   scp -r hackathon1 ubuntu@<EC2_IP>:~/
#   ssh ubuntu@<EC2_IP>
#   cd hackathon1 && chmod +x deploy/ec2-setup.sh && ./deploy/ec2-setup.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"

echo
echo "Docker installed. Log out and back in (or run 'newgrp docker') for group changes to apply."
echo "Next: copy .env.example to .env, fill in real secrets, then run:"
echo "  docker compose up -d --build"
