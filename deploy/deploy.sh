#!/usr/bin/env bash
set -euo pipefail

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root (using sudo)." >&2
  exit 1
fi

echo "=== Step 1: Install System Packages ==="
apt-get update -y
apt-get install -y python3 python3-venv mariadb-server nginx

echo "=== Step 2: Create System and User Accounts ==="
# 1. student (sudo privileges, no password)
if ! id "student" &>/dev/null; then
  useradd -m -s /bin/bash student
  echo "User 'student' created."
fi
echo "student ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/student
chmod 0440 /etc/sudoers.d/student

# 2. teacher (sudo privileges, password '12345678', change on login)
if ! id "teacher" &>/dev/null; then
  useradd -m -s /bin/bash teacher
  echo "User 'teacher' created."
fi
echo "teacher:12345678" | chpasswd
chage -d 0 teacher
usermod -aG sudo teacher

# 3. operator (restricted sudo, password '12345678', change on login)
if ! id "operator" &>/dev/null; then
  useradd -m -s /bin/bash operator
  echo "User 'operator' created."
fi
echo "operator:12345678" | chpasswd
chage -d 0 operator

# Sudo rules for operator (ONLY systemctl start/stop/restart/status mywebapp AND systemctl reload nginx)
cat << 'EOF' > /etc/sudoers.d/operator
operator ALL=(ALL) NOPASSWD: /usr/bin/systemctl start mywebapp, /usr/bin/systemctl stop mywebapp, /usr/bin/systemctl restart mywebapp, /usr/bin/systemctl status mywebapp, /usr/bin/systemctl reload nginx
EOF
chmod 0440 /etc/sudoers.d/operator

# 4. mywebapp (system user for running the service, no shell)
if ! id "mywebapp" &>/dev/null; then
  useradd -r -s /usr/sbin/nologin mywebapp
  echo "System user 'mywebapp' created."
fi

echo "=== Step 3: Configure MariaDB Database ==="
systemctl start mariadb
systemctl enable mariadb

# Create DB and user 'app_user' with password 'app_password'
mysql -e "CREATE DATABASE IF NOT EXISTS inventory_db;"
mysql -e "CREATE USER IF NOT EXISTS 'app_user'@'localhost' IDENTIFIED BY 'app_password';"
mysql -e "GRANT ALL PRIVILEGES ON inventory_db.* TO 'app_user'@'localhost';"
mysql -e "CREATE USER IF NOT EXISTS 'app_user'@'127.0.0.1' IDENTIFIED BY 'app_password';"
mysql -e "GRANT ALL PRIVILEGES ON inventory_db.* TO 'app_user'@'127.0.0.1';"
mysql -e "FLUSH PRIVILEGES;"
echo "Database inventory_db and user app_user configured."

echo "=== Step 4: Deploy Web Application Code ==="
mkdir -p /opt/mywebapp

# Find the repository parent directory relative to where the deploy script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Copy files to deployment target
cp -r "$REPO_ROOT/app" /opt/mywebapp/
cp "$REPO_ROOT/requirements.txt" /opt/mywebapp/

# Create venv and install dependencies
python3 -m venv /opt/mywebapp/.venv
/opt/mywebapp/.venv/bin/pip install --upgrade pip
/opt/mywebapp/.venv/bin/pip install -r /opt/mywebapp/requirements.txt

# Adjust file ownership and permissions for safety
chown -R mywebapp:mywebapp /opt/mywebapp
chmod -R 750 /opt/mywebapp

echo "=== Step 5: Configure Systemd Socket Activation ==="
cp "$REPO_ROOT/deploy/mywebapp.service" /etc/systemd/system/
cp "$REPO_ROOT/deploy/mywebapp.socket" /etc/systemd/system/

systemctl daemon-reload
systemctl enable mywebapp.socket
systemctl start mywebapp.socket
echo "Systemd socket activation configured and started."

echo "=== Step 6: Configure Nginx Reverse Proxy ==="
cp "$REPO_ROOT/deploy/nginx.conf" /etc/nginx/sites-available/mywebapp
ln -sf /etc/nginx/sites-available/mywebapp /etc/nginx/sites-enabled/mywebapp
rm -f /etc/nginx/sites-enabled/default

systemctl enable nginx
systemctl start nginx
nginx -t && systemctl reload nginx
echo "Nginx configured and reloaded."

echo "=== Step 7: Create Student Gradebook ==="
mkdir -p /home/student
echo "26" > /home/student/gradebook
chown student:student /home/student/gradebook
chmod 644 /home/student/gradebook
echo "Gradebook for student created with variant number 26."

echo "=== Step 8: Lock Default User Account ==="
if id "ubuntu" &>/dev/null; then
  usermod -L ubuntu
  echo "Default system user 'ubuntu' has been locked."
else
  echo "User 'ubuntu' not found, skipping user locking."
fi

echo "=== Deployment Completed Successfully! ==="
