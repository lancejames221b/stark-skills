# Diagnostic Commands Reference

Quick reference for read-only diagnostic commands organized by investigation type.

## Service Status

### Systemd Services
```bash
# Check service status
systemctl status <service-name>

# See if service is enabled
systemctl is-enabled <service-name>

# List all failed services
systemctl --failed

# Check service dependencies
systemctl list-dependencies <service-name>
```

### Docker Containers
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Container details
docker inspect <container-name>

# Container resource usage
docker stats --no-stream <container-name>

# Container processes
docker top <container-name>
```

### Kubernetes
```bash
# Get pods in namespace
kubectl get pods -n <namespace>

# Describe pod (full details)
kubectl describe pod <pod-name> -n <namespace>

# Get pod resource usage
kubectl top pod <pod-name> -n <namespace>

# Get events (recent issues)
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Check node health
kubectl get nodes
kubectl describe node <node-name>
```

## Logs

### Systemd Logs
```bash
# Recent logs for service
journalctl -u <service> --since "10 minutes ago"

# Last 100 lines
journalctl -u <service> -n 100

# Follow logs (real-time)
journalctl -u <service> -f

# Filter by priority (error, warning)
journalctl -u <service> -p err -n 50
```

### Docker Logs
```bash
# Last 100 lines
docker logs --tail 100 <container>

# Follow logs
docker logs -f <container>

# Logs with timestamps
docker logs -t --tail 50 <container>

# Logs since specific time
docker logs --since 10m <container>
```

### Kubernetes Logs
```bash
# Pod logs (last 100 lines)
kubectl logs -n <namespace> <pod> --tail=100

# Specific container in pod
kubectl logs -n <namespace> <pod> -c <container> --tail=100

# Previous crashed container
kubectl logs -n <namespace> <pod> --previous

# All pods with label
kubectl logs -n <namespace> -l app=<name> --tail=20
```

### Application Logs
```bash
# Tail specific log file
tail -n 100 /var/log/<app>/<logfile>

# Search logs for errors
grep -i error /var/log/<app>/<logfile> | tail -20

# Multiple files by timestamp
ls -lt /var/log/<app>/ | head -5
```

## Resource Usage

### Disk
```bash
# Disk space
df -h

# Disk usage by directory
du -sh /path/to/directory/*

# Inodes usage
df -i

# Find large files
find /path -type f -size +100M -exec ls -lh {} \;
```

### Memory
```bash
# Memory overview
free -h

# Detailed memory info
cat /proc/meminfo

# Top memory consumers
ps aux --sort=-%mem | head -10
```

### CPU
```bash
# CPU info
lscpu

# Load average
uptime

# Top CPU consumers
ps aux --sort=-%cpu | head -10

# Interactive top
top -bn1 | head -20
```

### Processes
```bash
# All processes
ps aux

# Process tree
pstree -p

# Find process by name
ps aux | grep <name>

# Process details
cat /proc/<pid>/status
```

## Network

### Connections
```bash
# Listening ports
ss -tulpn
netstat -tulpn

# Established connections
ss -tan | grep ESTAB

# Specific port
ss -tulpn | grep :<port>
```

### Connectivity
```bash
# Test connectivity
ping -c 4 <host>

# DNS lookup
nslookup <domain>
dig <domain>

# Trace route
traceroute <host>

# Check if port is open
nc -zv <host> <port>
```

### Firewall
```bash
# UFW status
sudo ufw status verbose

# iptables rules
sudo iptables -L -n -v

# Active connections by IP
ss -tan | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr
```

## Configuration

### Files
```bash
# View config (don't modify)
cat /etc/<service>/config.conf

# Check syntax (if available)
nginx -t
apache2ctl -t

# Compare with backup
diff /etc/<service>/config.conf /etc/<service>/config.conf.bak
```

### Git
```bash
# Recent commits
git log --oneline -10

# Changes since last deploy
git log --since="1 day ago" --oneline

# Current branch and status
git status

# Show specific commit
git show <commit-hash>
```

### Docker Images
```bash
# List images
docker images

# Image history
docker history <image>

# Inspect image
docker inspect <image>
```

## Database (Read-Only)

### PostgreSQL
```bash
# Connect
psql -U <user> -d <database>

# Query within psql:
\dt           # List tables
\d <table>    # Describe table
\l            # List databases
\du           # List users

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Slow queries (if pg_stat_statements enabled)
SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

### MySQL/MariaDB
```bash
# Connect
mysql -u <user> -p <database>

# Within mysql:
SHOW DATABASES;
SHOW TABLES;
DESCRIBE <table>;
SHOW PROCESSLIST;

# Slow queries
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

## Security

### System Users
```bash
# List users
cat /etc/passwd

# Currently logged in
who
w

# Login history
last -n 20

# Failed login attempts
sudo lastb -n 20
```

### Permissions
```bash
# File permissions
ls -la /path/to/file

# Directory permissions
ls -ld /path/to/directory

# Find files with specific permissions
find /path -perm <mode>

# SUID/SGID files
find / -perm /6000 -type f 2>/dev/null
```

### Security Logs
```bash
# Auth logs
sudo tail -100 /var/log/auth.log

# Sudo commands
sudo grep sudo /var/log/auth.log | tail -20

# SSH attempts
sudo grep sshd /var/log/auth.log | tail -30
```

## Performance

### Response Times
```bash
# HTTP request timing
time curl -o /dev/null -s -w '%{time_total}\n' https://example.com

# Multiple requests average
for i in {1..10}; do time curl -o /dev/null -s https://example.com; done
```

### DNS
```bash
# DNS query time
time nslookup example.com

# Check nameservers
cat /etc/resolv.conf
```

## Quick System Overview

### One-Liner Health Checks
```bash
# Load, memory, disk at once
uptime && free -h && df -h

# Failed systemd services
systemctl --failed --no-pager

# Listening ports
ss -tulpn | grep LISTEN

# Top 5 CPU processes
ps aux --sort=-%cpu | head -6

# Top 5 memory processes
ps aux --sort=-%mem | head -6

# Recent system errors
journalctl -p err -n 20 --no-pager
```

## Remember

All these commands are **READ-ONLY**. Survey mode means:
- ✅ Run these commands to gather info
- ✅ Analyze output and identify issues
- ❌ Don't modify configs
- ❌ Don't restart services
- ❌ Don't make changes

Report findings, suggest actions, but **wait for permission** before executing fixes.
