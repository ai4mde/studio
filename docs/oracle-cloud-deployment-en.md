# Oracle Cloud Deployment Guide

This document covers the full process of deploying Studio to Oracle Cloud Always Free Tier.

---

## Resource Usage vs. Free Tier Limits

| Resource | Free Tier Limit | Current Usage | Remaining |
|---|---|---|---|
| A1 OCPU | 4 total | 1 | **3 left** |
| A1 RAM | 24 GB total | 1 GB | **23 GB left** |
| Block Storage | 200 GB | ~50 GB (boot vol) | ~150 GB left |
| Outbound data | 10 TB/mo | minimal | ~10 TB left |

> **Recommendation**: You are barely using your free quota. Upgrade the VM to **4 OCPU / 24 GB RAM** at zero cost — it will fix all the OOM build failures and make the server much faster. Steps: Oracle Console → Instance → **Edit** → change shape to 4 OCPU / 24 GB RAM → save. The VM will reboot.

---

## Architecture

- **Host**: Oracle Cloud Ampere A1 (ARM, permanently free)
- **Domain**: nip.io automatic DNS (no domain purchase needed)
- **Reverse proxy**: Traefik v3
- **CI/CD**: GitHub Actions → SSH → `docker compose`
- **URL pattern**: `http://ai4mde.<VM_IP>.nip.io`

---

## Step 1 — Create the Oracle Cloud VM

1. Log into [cloud.oracle.com](https://cloud.oracle.com)
2. **Compute → Instances → Create instance**
3. Configure:
   - **Image**: Ubuntu 22.04
   - **Shape**: VM.Standard.A1.Flex (Ampere, Always Free)
   - **OCPU**: 4, **RAM**: 24 GB *(use the full free quota)*
   - **SSH key**: paste the deploy public key (see below)
4. Note the **Public IP** after it boots

### Assign a Public IP

After the VM is created, the public IP is not assigned by default:

1. Instance page → **Primary VNIC**
2. Click the VNIC → **IP Addresses**
3. Click **Edit** on the Public IP row → select **Ephemeral** → confirm

### Open Port 80 in the Security List

1. Go to **subnet → Default Security List → Add Ingress Rules**
2. Add:
   - Source CIDR: `0.0.0.0/0`
   - Protocol: TCP
   - Destination Port: `80`

> Port 22 (SSH) is open by default. Do not remove it.

---

## Step 2 — SSH Deploy Key

Generate once on your local machine:

```bash
ssh-keygen -t ed25519 -C "oracle-deploy" -f ~/.ssh/oracle_studio_deploy -N ""
```

- **Public key** (`~/.ssh/oracle_studio_deploy.pub`) → paste into Oracle Cloud VM SSH Keys during instance creation
- **Private key** (`~/.ssh/oracle_studio_deploy`) → add to GitHub Secrets (see below)

---

## Step 3 — GitHub Secrets

Go to `github.com/<org>/studio/settings/secrets/actions` and add three secrets:

| Secret name | Value |
|---|---|
| `ORACLE_HOST` | VM public IP (e.g. `158.178.158.62`) |
| `ORACLE_USER` | `ubuntu` |
| `ORACLE_SSH_KEY` | Full contents of `~/.ssh/oracle_studio_deploy` |

---

## Step 4 — VM First-Time Setup

SSH into the VM and run the following.

### Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
sudo systemctl enable --now docker
```

> This takes 3–5 minutes. The apt lock will be held during install — do not retry.

### Clone the repo

```bash
git clone --branch develop-uilayout-revise \
  https://github.com/ai4mde/studio.git ~/studio
```

### Create secrets.env

```bash
cp ~/studio/config/secrets.env.example ~/studio/config/secrets.env
nano ~/studio/config/secrets.env
# Fill in GOOGLE_API_KEY, OPENAI_API_KEY, etc.
```

### Write .env with the VM's public IP

```bash
echo "ORACLE_IP=$(curl -s ifconfig.me)" > ~/studio/.env
```

### Add swap (critical if using 1 GB RAM)

If you upgraded to 4 OCPU / 24 GB RAM, skip this. Otherwise:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Open port 80 at the OS level

Oracle's Security List is a network-level firewall; the OS-level firewall also needs updating:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo sh -c 'iptables-save > /etc/iptables/rules.v4'
```

---

## Step 5 — First Build and Launch

### Build services one at a time

Building all four services in parallel exhausts RAM on small instances. Build sequentially using `nohup` so the process survives SSH disconnects:

```bash
cd ~/studio
nohup bash -c '
  sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml build studio-api
  sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml build studio-prototypes
  sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml build gemini-make-agent
  sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml build studio
  echo BUILD_DONE
' > /tmp/build.log 2>&1 &
```

Watch progress:

```bash
tail -f /tmp/build.log
```

> **First build time**: ~60–90 min on 1 OCPU ARM (downloads Node 18, Python 3.12 base images from scratch)
> **Subsequent builds**: ~5–10 min (Docker layer cache)

### Start all containers

```bash
cd ~/studio
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up -d
```

### Run DB migrations

```bash
sudo docker exec studio-studio-api-1 \
  python /usr/src/model/manage.py migrate --run-syncdb
```

---

## Step 6 — Verify

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'
```

All 6 containers should be Running:

```
traefik
studio-postgres-1
studio-studio-api-1
studio-studio-prototypes-1
studio-gemini-make-agent-1
studio-studio-1
```

| Service | URL |
|---|---|
| Frontend | `http://ai4mde.<IP>.nip.io` |
| API | `http://api.ai4mde.<IP>.nip.io` |
| Prototype | `http://prototype.ai4mde.<IP>.nip.io` |

Default login: `admin` / `sequoias`

---

## Step 7 — CI/CD (automatic on every push)

Every push to `develop-uilayout-revise` triggers the GitHub Action which:

1. SSHs into the VM
2. Runs `git pull`
3. Writes `ORACLE_IP` to `.env`
4. Runs `docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up --build -d`
5. Prunes old images with `docker image prune -f`

Workflow file: `.github/workflows/deploy-demo.yml`

---

## Known Issues and Fixes

### `npm run build` OOM — JavaScript heap out of memory

**Cause**: Node.js default heap is ~1.5 GB; insufficient on a 1 GB RAM VM.

**Fix**: `frontend/Dockerfile` — add before the build step:

```dockerfile
ENV NODE_OPTIONS=--max-old-space-size=1536
```

### Vite dev server blocks external hostname

**Cause**: Vite 4.5.13 includes a CVE-2025-31125 security backport that blocks non-localhost hosts by default.

**Fix**: `frontend/vite.config.ts`:

```ts
server: {
    allowedHosts: true,   // "all" string does NOT work in 4.5.x — must be boolean true
},
```

### SSH times out during build

**Cause**: 1 OCPU ARM VM hits 100% CPU during Docker builds; the SSH daemon cannot accept new connections.

**Fix**: Wait for the build to finish. Verify the instance is still `Running` in Oracle Console. This is expected behavior, not an error.

### Build killed when SSH session drops

**Cause**: Child processes receive SIGHUP when the SSH session closes.

**Fix**: Always start long-running builds with `nohup ... &` and log to `/tmp/build.log`.

### `git pull` blocked by local changes

**Cause**: Files were edited directly on the VM without committing.

**Fix**:

```bash
git checkout -- <modified-file>
git pull
```

---

## Day-to-Day Commands

```bash
# Check all containers
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Stream logs for a container
sudo docker logs studio-studio-api-1 --tail 50 -f

# Manual redeploy
cd ~/studio
git pull origin develop-uilayout-revise
echo "ORACLE_IP=$(curl -s ifconfig.me)" > .env
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up --build -d
sudo docker image prune -f

# Restart a single container
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml restart studio-studio-1
```
