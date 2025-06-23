# Monitoring Guide

## Overview

The IMS Integration Service includes comprehensive monitoring capabilities that work across cloud providers (AWS, Azure, etc.) without vendor lock-in.

## Monitoring Stack

### 1. Application Metrics (Prometheus)

Built-in metrics exposed at `/api/metrics`:

#### Transaction Metrics
- **ims_transactions_total**: Counter of all transactions
  - Labels: `transaction_type`, `source`, `status`
  - Example: `ims_transactions_total{transaction_type="new",source="triton",status="completed"}`

- **ims_transaction_duration_seconds**: Histogram of processing times
  - Labels: `transaction_type`, `source`
  - Useful for identifying performance issues

- **ims_active_transactions**: Gauge showing current processing count
  - No labels
  - Monitor for queue buildup

#### System Metrics
- **ims_connection_status**: IMS connection health (1=connected, 0=disconnected)
- **ims_errors_total**: Error counter by type and source

### 2. Health Checks

Enhanced health endpoint at `/api/health`:

```bash
# Check health
curl http://localhost:8000/api/health

# Example response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {"status": "healthy", "message": "Database connection active"},
    "ims_connection": {"status": "healthy", "message": "IMS connection active"},
    "disk_space": {"status": "healthy", "message": "Sufficient disk space"},
    "memory": {"status": "healthy", "message": "Memory usage normal"}
  },
  "metrics": {
    "active_transactions": 5,
    "ims_connected": true
  }
}
```

### 3. Distributed Tracing (OpenTelemetry)

Optional but recommended for production environments.

#### Configuration
```bash
# .env
OTEL_EXPORTER_OTLP_ENDPOINT=http://your-collector:4317
```

#### Supported Backends
- **AWS**: X-Ray via ADOT Collector
- **Azure**: Application Insights
- **Self-hosted**: Jaeger, Zipkin
- **SaaS**: Datadog, New Relic, Honeycomb

## Setting Up Monitoring

### Local Development

1. Start with monitoring profile:
```bash
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

2. Access dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Production - AWS

#### CloudWatch Integration
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure for Prometheus metrics
# /opt/aws/amazon-cloudwatch-agent/etc/prometheus.yml
scrape_configs:
  - job_name: 'ims-integration'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics'
```

#### X-Ray Tracing
```bash
# Set environment variable
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Run ADOT collector
docker run -d \
  -p 4317:4317 \
  -v $(pwd)/adot-config.yaml:/etc/otel-config.yaml \
  public.ecr.aws/aws-observability/aws-otel-collector:latest
```

### Production - Azure

#### Application Insights
```python
# No code changes needed! Just configure:
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-region.in.applicationinsights.azure.com/v2/track
```

#### Azure Monitor Metrics
- Metrics automatically collected via Application Insights
- Create alerts in Azure Portal

## Grafana Dashboard

Import our pre-built dashboard:

1. Open Grafana (http://localhost:3000)
2. Go to Dashboards → Import
3. Upload: `monitoring/grafana/dashboards/ims-integration.json`

Key panels:
- Transaction rate by type
- Success/failure rates
- Processing duration (P50, P95, P99)
- Active transactions
- Error rate
- IMS connection status

## Alerting

### Prometheus Alerts

Create `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: ims-integration
    rules:
      - alert: HighErrorRate
        expr: rate(ims_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: IMSConnectionDown
        expr: ims_connection_status == 0
        for: 1m
        annotations:
          summary: "IMS connection is down"
          
      - alert: HighTransactionQueueDepth
        expr: ims_active_transactions > 100
        for: 10m
        annotations:
          summary: "Transaction queue depth is high"
```

### CloudWatch Alarms (AWS)

```bash
# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name "IMS-High-Error-Rate" \
  --alarm-description "Alert when error rate exceeds threshold" \
  --metric-name ims_errors_total \
  --namespace "IMS-Integration" \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Logging

### Structured Logging

The service uses structured JSON logging:

```python
logger.info("Transaction processed", extra={
    "transaction_id": "123",
    "type": "new",
    "source": "triton",
    "duration": 1.23
})
```

### Log Aggregation

#### AWS CloudWatch Logs
```bash
# Docker driver configuration in docker-compose.prod.yml
logging:
  driver: awslogs
  options:
    awslogs-group: ims-integration
    awslogs-region: us-east-1
```

#### Azure Container Insights
```bash
# Similar configuration for Azure
logging:
  driver: fluentd
  options:
    fluentd-address: localhost:24224
```

## Performance Monitoring

### Key Metrics to Watch

1. **Transaction Processing Time**
   - Target: < 5 seconds for 95th percentile
   - Alert if P99 > 30 seconds

2. **Error Rate**
   - Target: < 0.1%
   - Alert if > 1% over 5 minutes

3. **Queue Depth**
   - Target: < 50 active transactions
   - Alert if > 100 for 10 minutes

### Optimization Tips

1. **Slow Transactions**
   - Check IMS response times in logs
   - Review transaction complexity
   - Consider batch processing

2. **High Memory Usage**
   - Monitor container memory via Docker stats
   - Check for memory leaks in long-running processes
   - Increase container limits if needed

## Troubleshooting

### No Metrics Appearing

1. Check endpoint is accessible:
```bash
curl http://localhost:8000/api/metrics
```

2. Verify Prometheus configuration:
```bash
docker-compose -f docker-compose.prod.yml logs prometheus
```

### Missing Traces

1. Verify OTLP endpoint:
```bash
telnet your-collector 4317
```

2. Check for errors in logs:
```bash
grep -i "telemetry\|otel" ims_integration.log
```

### High Cardinality Issues

Avoid dynamic label values that can cause metric explosion:
- ❌ Bad: `transaction_id` as label
- ✅ Good: `transaction_type`, `source`, `status`