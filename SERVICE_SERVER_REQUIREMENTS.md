# Server Requirements for IMS Integration Service

## Required Software Packages

### For Docker Deployment (Recommended)

1. **Docker Engine** (version 20.10.0 or higher)
   - Official Docker CE/EE
   - Required for running containers

2. **Docker Compose** (version 2.0.0 or higher)
   - For multi-container orchestration
   - Can be installed as Docker plugin or standalone

3. **curl** or **wget**
   - For downloading deployment scripts
   - Usually pre-installed

4. **systemd** (for auto-restart)
   - Standard on Ubuntu/RHEL
   - Required for service management

### Operating System
- **Ubuntu Server 22.04 LTS** (recommended)
- **Ubuntu Server 20.04 LTS** (supported)
- **RHEL 8/9** (supported)
- **Amazon Linux 2** (supported)

## Network Requirements

### Outbound Connections Required

| Destination | Port | Protocol | Purpose |
|------------|------|----------|---------|
| dc02imsws01.rsgcorp.local | 80, 9213 | HTTP | IMS One SOAP API |
| ws2.mgasystems.com | 443 | HTTPS | ISCMGA Test SOAP API |
| registry.docker.io | 443 | HTTPS | Docker image pulls |
| production.cloudflare.docker.com | 443 | HTTPS | Docker registry |

### Inbound Connections (from authorized sources only)

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | HTTP | API endpoint |
| 9090 | HTTP | Prometheus metrics (optional) |
| 3000 | HTTP | Grafana dashboard (optional) |

## Firewall Rules

```bash
# Required outbound
iptables -A OUTPUT -p tcp --dport 80 -d dc02imsws01.rsgcorp.local -j ACCEPT
iptables -A OUTPUT -p tcp --dport 9213 -d dc02imsws01.rsgcorp.local -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d ws2.mgasystems.com -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d registry.docker.io -j ACCEPT

# Required inbound (adjust source IPs as needed)
iptables -A INPUT -p tcp --dport 8000 -s <authorized_network> -j ACCEPT
```

## Storage Requirements

- **/opt/ims-integration**: 5 GB minimum for application
- **/var/lib/docker**: 20 GB minimum for Docker images/containers
- **/var/log**: 10 GB recommended for logs

## User/Permission Requirements

1. **Service Account**: Non-root user (e.g., 'ims-service')
2. **Docker Group**: User must be in 'docker' group
3. **Directory Ownership**: /opt/ims-integration owned by service user

```bash
# Create service user
sudo useradd -r -s /bin/bash ims-service
sudo usermod -aG docker ims-service

# Create and set ownership
sudo mkdir -p /opt/ims-integration
sudo chown -R ims-service:ims-service /opt/ims-integration
```

## Installation Commands for Corporate Team

### Ubuntu 22.04 Installation

```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install -y docker.io docker-compose

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker-compose --version
```

### RHEL 8/9 Installation

```bash
# Install Docker
sudo yum install -y docker docker-compose

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker-compose --version
```

## Security Considerations

1. **No root access** required for application
2. **SELinux**: Compatible (may need contexts for /opt/ims-integration)
3. **AppArmor**: Compatible (Ubuntu default)
4. **Secrets**: Stored in .env file with 600 permissions

## Monitoring Dependencies (Optional)

If using built-in monitoring:
- **Prometheus**: Runs in container (no host install needed)
- **Grafana**: Runs in container (no host install needed)

If integrating with corporate monitoring:
- Expose port 8000/api/metrics for Prometheus scraping
- Expose port 8000/api/health for health checks

## DNS Requirements

Server must resolve:
- Internal IMS hostnames (dc02imsws01.rsgcorp.local)
- External hostnames (ws2.mgasystems.com)
- Docker registry (registry.docker.io)

## Summary for Deployment Team

**Minimal installation needed:**
1. Docker and Docker Compose
2. Open firewall ports (outbound: 80, 443, 9213)
3. Create service user with docker group access
4. Ensure DNS resolution for IMS servers
5. Allocate storage (/opt/ims-integration, /var/lib/docker)

**We do NOT need:**
- Python (runs in container)
- MySQL client (runs in container)
- Any application dependencies (all in container)
- Root access after initial setup

**Deployment is just:**
```bash
sudo ./deploy.sh
```

That's it!