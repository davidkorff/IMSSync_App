# Cloud Deployment Guide

This guide covers deploying the IMS Integration Service to cloud environments with a focus on portability between AWS and Azure.

## Overview

The service is containerized using Docker and includes cloud-agnostic monitoring through OpenTelemetry and Prometheus. This design allows easy migration between cloud providers without code changes.

## Architecture Components

1. **Docker Container**: FastAPI application with all dependencies
2. **Health Checks**: Enhanced endpoint at `/api/health` with detailed status
3. **Metrics**: Prometheus metrics at `/api/metrics`
4. **OpenTelemetry**: Cloud-agnostic distributed tracing (optional)
5. **Auto-restart**: Systemd service configuration

## Deployment Options

### Option 1: Direct EC2/VM Deployment (Recommended)

Best for single-instance deployments that need to migrate between clouds.

#### AWS EC2 Setup

```bash
# 1. Launch EC2 instance (Ubuntu 22.04 recommended)
# 2. SSH into instance
# 3. Clone repository
git clone <repository-url>
cd ims-integration

# 4. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 5. Run deployment script
sudo ./deploy.sh
```

#### Azure VM Setup (Future Migration)

```bash
# Same steps as AWS - no changes needed!
# The deploy.sh script works on both platforms
```

### Option 2: Container Services

#### AWS ECS
- Use existing Dockerfile
- Create ECS task definition
- Configure CloudWatch logging

#### Azure Container Instances (Future)
- Same Docker image
- Deploy using Azure CLI or Portal
- Configure Azure Monitor

## Monitoring Configuration

### 1. Built-in Metrics (Always Available)

The service exposes Prometheus metrics at `/api/metrics`:

- `ims_transactions_total`: Transaction counts by type and status
- `ims_transaction_duration_seconds`: Processing time histograms
- `ims_active_transactions`: Currently processing transactions
- `ims_connection_status`: IMS connection health
- `ims_errors_total`: Error counts by type

### 2. OpenTelemetry (Optional)

Configure distributed tracing by setting:

```bash
# .env file
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
```

Works with:
- AWS X-Ray (via ADOT Collector)
- Azure Application Insights
- Jaeger, Zipkin, or any OTLP-compatible backend

### 3. Prometheus + Grafana (Optional)

Start with monitoring profile:

```bash
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

Access:
- Prometheus: http://your-server:9090
- Grafana: http://your-server:3000 (default login: admin/admin)

## Health Monitoring

Enhanced health endpoint provides:

```json
GET /api/health

{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection active"
    },
    "ims_connection": {
      "status": "healthy",
      "message": "IMS connection active"
    },
    "disk_space": {
      "status": "healthy",
      "message": "Sufficient disk space"
    },
    "memory": {
      "status": "healthy",
      "message": "Memory usage normal"
    }
  },
  "metrics": {
    "active_transactions": 5,
    "ims_connected": true
  }
}
```

## Production Configuration

### Environment Variables

```bash
# Cloud provider (aws or azure)
CLOUD_PROVIDER=aws  # Change to 'azure' when migrating

# Environment
ENVIRONMENT=production

# Optional: OpenTelemetry endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317

# Optional: Grafana password
GRAFANA_PASSWORD=secure-password
```

### Security Considerations

1. **API Key**: Ensure `API_KEY` is set in production
2. **TLS/SSL**: Use reverse proxy (nginx) or cloud load balancer
3. **Network**: Restrict access to monitoring endpoints
4. **Secrets**: Use cloud secret managers (AWS Secrets Manager, Azure Key Vault)

## Deployment Commands

### Start Service
```bash
sudo systemctl start ims-integration
```

### Stop Service
```bash
sudo systemctl stop ims-integration
```

### View Logs
```bash
# System logs
sudo journalctl -u ims-integration -f

# Docker logs
docker logs ims-integration_api_1
```

### Update Service
```bash
cd /opt/ims-integration
git pull
docker-compose -f docker-compose.prod.yml build
sudo systemctl restart ims-integration
```

## Migration Checklist

When moving from AWS to Azure:

1. [ ] Update `CLOUD_PROVIDER=azure` in .env
2. [ ] Point OTEL endpoint to Azure Monitor (if using)
3. [ ] Update DNS/load balancer configuration
4. [ ] Copy .env file with credentials
5. [ ] Run same deployment script

No code changes required!

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u ims-integration -n 100

# Check Docker
docker-compose -f docker-compose.prod.yml logs
```

### High Memory Usage
- Check `/api/health` endpoint
- Review active transactions in metrics
- Consider increasing instance size

### Connection Issues
- Verify security groups/network rules
- Check IMS credentials in .env
- Review health check status