# Oracle Cloud 部署指南

本文記錄將 Studio 部署到 Oracle Cloud Always Free Tier 的完整流程。

---

## 架構概覽

- **主機**: Oracle Cloud Ampere A1（ARM，永久免費）
- **Domain**: nip.io 自動 DNS（無需購買網域）
- **反向代理**: Traefik v3
- **CI/CD**: GitHub Actions → SSH → `docker compose`
- **URL 格式**: `http://ai4mde.<VM_IP>.nip.io`

---

## 一、建立 Oracle Cloud VM

1. 登入 [cloud.oracle.com](https://cloud.oracle.com)
2. **Compute → Instances → Create instance**
3. 設定：
   - **Image**: Ubuntu 22.04
   - **Shape**: VM.Standard.A1.Flex（Ampere，Always Free）
   - **OCPU**: 1、**RAM**: 6 GB（預設可能是 1 GB，記得改成 6 GB）
   - **SSH key**: 貼入 deploy public key（見下方）
4. 建好後記下 **Public IP**

### 指定 Public IP

VM 建好後 Public IP 預設未分配：

1. 進 instance → **Primary VNIC**
2. 點進 VNIC → **IP Addresses**
3. Public IP 那行點 **Edit** → 選 **Ephemeral** → 確認

### 開放 Port 80

1. 進 **subnet → Default Security List → Add Ingress Rules**
2. 加入：
   - Source CIDR: `0.0.0.0/0`
   - Protocol: TCP
   - Destination Port: `80`

> **注意**：port 22 (SSH) 預設已開放，不需要另外加。

---

## 二、SSH Deploy Key

在本地生成一次性的 deploy key：

```bash
ssh-keygen -t ed25519 -C "oracle-deploy" -f ~/.ssh/oracle_studio_deploy -N ""
```

- **Public key** → 貼入 Oracle Cloud VM 的 SSH Keys
- **Private key** → 加入 GitHub Secrets（見下方）

---

## 三、GitHub Secrets

到 `github.com/<org>/studio/settings/secrets/actions` 加入三個 Secret：

| Secret 名稱 | 值 |
|---|---|
| `ORACLE_HOST` | VM 的 Public IP（e.g. `158.178.158.62`） |
| `ORACLE_USER` | `ubuntu` |
| `ORACLE_SSH_KEY` | `~/.ssh/oracle_studio_deploy` 的完整內容 |

---

## 四、VM 初始化

第一次 SSH 進 VM 後執行：

### 1. 安裝 Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
sudo systemctl enable --now docker
```

> 安裝過程約 3-5 分鐘，apt lock 期間不要重複執行。

### 2. Clone Repo

```bash
git clone --branch develop-uilayout-revise \
  https://github.com/ai4mde/studio.git ~/studio
```

### 3. 建立 secrets.env

```bash
cp ~/studio/config/secrets.env.example ~/studio/config/secrets.env
nano ~/studio/config/secrets.env
# 填入 GOOGLE_API_KEY, OPENAI_API_KEY 等
```

### 4. 建立 .env（含 VM IP）

```bash
echo "ORACLE_IP=$(curl -s ifconfig.me)" > ~/studio/.env
```

### 5. 加 Swap（重要：1 GB RAM 不夠 build）

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 6. 開放 OS 層 Port 80

Oracle Security List 是網路層防火牆，OS 層也要開：

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo sh -c 'iptables-save > /etc/iptables/rules.v4'
```

---

## 五、首次 Build 與啟動

### 逐個 Build（避免同時耗盡記憶體）

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

查看進度：

```bash
tail -f /tmp/build.log
```

> **首次 build 時間**：ARM 1 OCPU 約 60-90 分鐘（含下載 Node 18、Python 3.12 等 base image）
> **後續 build**：有 Docker cache，約 5-10 分鐘

### 啟動所有 Container

```bash
cd ~/studio
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up -d
```

### 執行 DB Migration

```bash
sudo docker exec studio-studio-api-1 \
  python /usr/src/model/manage.py migrate --run-syncdb
```

---

## 六、確認服務

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Status}}'
```

應看到 6 個 container Running：

```
traefik
studio-postgres-1
studio-studio-api-1
studio-studio-prototypes-1
studio-gemini-make-agent-1
studio-studio-1
```

訪問：

| 服務 | URL |
|---|---|
| Frontend | `http://ai4mde.<IP>.nip.io` |
| API | `http://api.ai4mde.<IP>.nip.io` |
| Prototype | `http://prototype.ai4mde.<IP>.nip.io` |

預設帳號：`admin` / `sequoias`

---

## 七、CI/CD（後續自動部署）

每次 push 到 `develop-uilayout-revise` branch，GitHub Actions 會自動：

1. SSH 進 VM
2. `git pull`
3. 寫入 `ORACLE_IP` 到 `.env`
4. `docker compose up --build -d`
5. `docker image prune -f`

Workflow 設定檔：`.github/workflows/deploy-demo.yml`

---

## 八、已知問題與解法

### `npm run build` OOM（JavaScript heap out of memory）

**原因**：VM RAM 只有 1 GB，Vite build 需要更多 heap。

**解法**：`frontend/Dockerfile` 加入：

```dockerfile
ENV NODE_OPTIONS=--max-old-space-size=1536
```

### Vite dev server 拒絕外部 hostname

**原因**：Vite 4.5.13 包含 CVE-2025-31125 安全補丁，預設封鎖非 localhost 的 host。

**解法**：`frontend/vite.config.ts` 加入：

```ts
server: {
    allowedHosts: true,
},
```

> 注意：`"all"` 字串在 4.5.x 無效，需用 `true`。

### SSH 連不進去（build 期間）

**原因**：1 OCPU ARM VM 在 build 時 CPU 100%，SSH daemon 無法回應新連線。

**解法**：等 build 完成，或從 Oracle console 確認 instance 是 Running，等待即可。

### Build 被中斷（SSH session 斷線）

**原因**：SSH session 斷線後，子 process 收到 SIGHUP 被殺。

**解法**：永遠用 `nohup ... &` 啟動 build，日誌寫到 `/tmp/build.log`。

### `git pull` 被 local 修改擋住

**原因**：直接在 VM 上修改了被 git 追蹤的檔案。

**解法**：

```bash
git checkout -- <file>
git pull
```

---

## 九、日常維護指令

```bash
# 查看所有 container 狀態
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# 查看某個 container 的 log
sudo docker logs studio-studio-api-1 --tail 50 -f

# 手動重新部署
cd ~/studio
git pull origin develop-uilayout-revise
echo "ORACLE_IP=$(curl -s ifconfig.me)" > .env
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml up --build -d
sudo docker image prune -f

# 重啟單一 container
sudo docker compose -f docker-compose.yaml -f docker-compose.cloud.yml restart studio-studio-1
```
