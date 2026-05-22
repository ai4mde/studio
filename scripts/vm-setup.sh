#!/usr/bin/env bash
# One-command Oracle Cloud VM setup.
# Run once after provisioning the VM:
#   bash <(curl -fsSL https://raw.githubusercontent.com/<org>/studio/develop-uilayout-revise/scripts/vm-setup.sh)
# Or copy the file to the VM and: bash scripts/vm-setup.sh
set -euo pipefail

# ── 1. Install Docker ──────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  echo "Docker installed. NOTE: you may need to log out and back in for group changes."
fi

# ── 2. Clone repo ──────────────────────────────────────────────────────────────
REPO_DIR="$HOME/studio"
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Cloning repository..."
  git clone --branch develop-uilayout-revise https://github.com/RuikeYuan/studio.git "$REPO_DIR"
fi

cd "$REPO_DIR"

# ── 3. Write config env files ──────────────────────────────────────────────────
# Copy secrets — edit these before running!
if [ ! -f config/secrets.env ]; then
  cp config/secrets.env.example config/secrets.env
  echo ""
  echo "⚠  Created config/secrets.env from example."
  echo "   Edit it now and add your GOOGLE_API_KEY / OPENAI_KEY etc., then re-run."
  exit 1
fi

# ── 4. Write .env with this VM's public IP ─────────────────────────────────────
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com)
echo "ORACLE_IP=${PUBLIC_IP}" > .env
echo "Detected public IP: ${PUBLIC_IP}"

# ── 5. Pull images and start stack ────────────────────────────────────────────
docker compose -f docker-compose.yaml -f docker-compose.cloud.yml pull --ignore-pull-failures || true
docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up --build -d
docker image prune -f

echo ""
echo "✅ Studio is running at:"
echo "   Frontend:  http://ai4mde.${PUBLIC_IP}.nip.io"
echo "   API:       http://api.ai4mde.${PUBLIC_IP}.nip.io"
echo "   Prototype: http://prototype.ai4mde.${PUBLIC_IP}.nip.io"
echo ""
echo "Add these GitHub Secrets to enable CI/CD:"
echo "   ORACLE_HOST = ${PUBLIC_IP}"
echo "   ORACLE_USER = $(whoami)"
echo "   ORACLE_SSH_KEY = (contents of your deploy private key)"
