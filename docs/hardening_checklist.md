# Host Hardening Checklist

## 3.2-a: Create non-root sudo user
- `sudo adduser trader`
- `sudo usermod -aG sudo trader`
- `sudo mkdir -p /home/trader/.ssh`
- `sudo cp ~/.ssh/authorized_keys /home/trader/.ssh/`
- `sudo chown -R trader:trader /home/trader/.ssh`

## 3.2-b: Disable root SSH login
- Edited `/etc/ssh/sshd_config`: changed `PermitRootLogin yes` → `PermitRootLogin no`
- `sudo systemctl restart ssh`  _(or `sudo service ssh restart` on Ubuntu)_

## 3.2-c: Set up UFW firewall
- `sudo ufw default deny incoming`
- `sudo ufw default allow outgoing`
- `sudo ufw allow 22`
- `sudo ufw allow 3000/tcp`
- `sudo ufw allow 9090/tcp`
- `sudo ufw enable`

## 3.2-d: Install fail2ban
- `sudo apt update && sudo apt install -y fail2ban`
- `sudo systemctl enable --now fail2ban`

## 3.2-e: Unattended security upgrades
- `sudo apt install -y unattended-upgrades`
- `sudo dpkg-reconfigure --priority=low unattended-upgrades`