# Hetzner VPS Deployment Guide

> Deploy the Coffee & Climate dashboard on a €4/month Hetzner VPS with daily auto-updates, HTTPS, and no GitHub data commits.

---

## Overview

Architecture on a single €3.79 CX22 instance:

```
User ──HTTPS──▶ Caddy reverse proxy ──▶ Streamlit (:8501)
                                              │
                                         reads from
                                              │
                                         data/raw/coffee_futures.parquet
                                              ▲
                                              │
                                   cron job (daily 2pm)
                                   python fetch_coffee.py --refresh
```

No ephemeral storage issues. No uploading data to GitHub. Runs 24/7.

---

## 1. Provision the VPS

1. Sign up at [hetzner.com/cloud](https://www.hetzner.com/cloud) (€10 free credit for new accounts)
2. Create a project → **Add Server**
   - **Location**: Helsinki or Nuremberg (cheapest bandwidth)
   - **Type**: CX22 (2 vCPU, 4 GB RAM, €3.79/mo)
   - **Image**: Ubuntu 24.04 LTS
   - **SSH Key**: Add your public key (generate one if you don't have it)
   - **Name**: `coffee-prices`
3. Note the server's IP address after creation

---

## 2. Initial Server Setup

```bash
# SSH into the server (replace IP)
ssh root@<your-server-ip>

# Create a non-root user
adduser coffee
usermod -aG sudo coffee

# Hardening: disable root SSH login
sed -i 's/^PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl restart sshd

# Install base dependencies
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git caddy
```

Exit root session and log back in as the `coffee` user:

```bash
ssh coffee@<your-server-ip>
```

---

## 3. Deploy the Application

```bash
# Clone the repository
cd ~
git clone https://github.com/lynamg-lab/CoffeePrices.git
cd CoffeePrices

# Create virtual environment and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Important**: The `requirements.txt` contains `.` which installs the local package. This will make `from src.data.fetch_coffee` importable without the sys.path hack. If the install works, you can remove the sys.path lines from `app.py` later.

---

## 4. Daily Data Refresh (Cron)

Set up a cron job to fetch fresh data after the US market closes (14:00 UTC):

```bash
crontab -e
```

Add this line (runs Monday–Friday):

```
0 14 * * 1-5 cd /home/coffee/CoffeePrices && /home/coffee/CoffeePrices/.venv/bin/python -c "from src.data.fetch_coffee import fetch_coffee; fetch_coffee(refresh=True)" >> /home/coffee/CoffeePrices/data/fetch.log 2>&1
```

This re-downloads from yfinance and saves to `data/raw/coffee_futures.parquet`. The existing Streamlit process reads the updated file on the next page load.

---

## 5. Streamlit as a Service (systemd)

Create a systemd service so Streamlit starts on boot and auto-restarts:

```bash
sudo nano /etc/systemd/system/coffee-dashboard.service
```

```
[Unit]
Description=Coffee Price Dashboard (Streamlit)
After=network.target

[Service]
Type=simple
User=coffee
WorkingDirectory=/home/coffee/CoffeePrices
ExecStart=/home/coffee/CoffeePrices/.venv/bin/streamlit run src/dashboard/app.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable coffee-dashboard
sudo systemctl start coffee-dashboard
sudo systemctl status coffee-dashboard  # verify running
```

---

## 6. HTTPS via Caddy

Create a Caddyfile for automatic HTTPS + subdomain:

```bash
sudo nano /etc/caddy/Caddyfile
```

```
coffee.yourdomain.com {
    reverse_proxy 127.0.0.1:8501
}
```

Replace `coffee.yourdomain.com` with your actual domain pointing to the server's IP. If you don't have a domain, you can use a free subdomain like `coffee-prices.serv00.net` or skip HTTPS and access via `http://<ip>:8501`.

Restart Caddy:

```bash
sudo systemctl restart caddy
```

Caddy auto-provisions a Let's Encrypt TLS certificate. Your app is now live at `https://coffee.yourdomain.com`.

---

## 7. How to Update the Code

After making changes locally and pushing to GitHub:

```bash
ssh coffee@<your-server-ip>
cd ~/CoffeePrices
git pull origin main
sudo systemctl restart coffee-dashboard
```

Optionally automate this with a GitHub webhook (later).

---

## 8. Useful Commands

```bash
# View Streamlit logs
journalctl -u coffee-dashboard -f

# Restart the dashboard
sudo systemctl restart coffee-dashboard

# Check cron job ran
tail -f ~/CoffeePrices/data/fetch.log

# Check disk usage (parquet files are tiny, <1 MB)
du -sh ~/CoffeePrices/data/

# Monitor system resources
htop
```

---

## 9. Security Notes

- **Firewall**: Hetzner's web console has a built-in firewall. Allow only ports 22 (SSH), 80 (HTTP), and 443 (HTTPS).
- **SSH keys only**: No password-based SSH login (done in step 2).
- **Caddy auto-HTTPS**: All traffic is encrypted via Let's Encrypt.
- **Regular updates**: Run `sudo apt update && sudo apt upgrade -y` monthly.

---

## 10. Cost Breakdown

| Item | Cost |
|------|------|
| Hetzner CX22 (4 GB RAM, 2 vCPU) | €3.79/month |
| Domain (optional, e.g. Namecheap) | ~€10/year |
| **Total** | **~€4.50/month** |

Alternative: Oracle Cloud Free Tier (4 ARM cores, 24 GB RAM — actually free forever) if you want €0. But Hetzner is simpler to set up.

---

*Once deployed, you can remove `data/raw/coffee_futures.parquet` from Git tracking — the server's cron job handles it from then on.*
