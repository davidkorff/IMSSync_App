# RSG Integration Service Deployment Guide

This guide provides instructions for deploying the RSG Integration service with an external-facing IP address to receive incoming transactions.

## Prerequisites

- Docker and Docker Compose installed
- Valid SSL certificate for your domain (for production)
- Open port 80/443 on your firewall
- Domain name pointing to your server IP (recommended)

## Deployment Options

There are two main options for deployment:

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RSG\ Integration
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your specific configuration
   ```

3. **Configure the domain**
   Edit `nginx/conf.d/default.conf` and replace `api.yourdomain.com` with your actual domain name.

4. **Add SSL certificates**
   Place your SSL certificates in the `nginx/ssl/` directory:
   - `server.crt`: Your domain certificate
   - `server.key`: Your private key

5. **Start the services**
   ```bash
   # Use Docker Compose to start the service
   docker-compose up -d
   ```

6. **Check the service**
   ```bash
   # Verify the services are running
   docker-compose ps
   
   # Check the logs
   docker-compose logs -f api
   ```

### Option 2: Direct Server Deployment

1. **Install Python 3.11**
   ```bash
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip
   ```

2. **Set up the application**
   ```bash
   # Create a virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Run the service**
   ```bash
   # Start the service using uvicorn
   python run_service.py --host 0.0.0.0 --port 8000
   ```

5. **Set up a reverse proxy (Nginx or Apache)**
   Configure your web server to proxy requests to the API service and handle SSL termination.

## Network Configuration

To expose your service to external systems, you need to:

1. **Configure your firewall** to allow incoming traffic on ports 80 and 443
2. **Set up port forwarding** on your router/gateway if the server is behind NAT
3. **Obtain a static IP address** or use a dynamic DNS service
4. **Register a domain name** pointing to your IP address (recommended)

## Security Considerations

1. **API Keys**: Generate strong API keys in your .env file:
   ```
   API_KEYS=["your-strong-api-key-1", "your-strong-api-key-2"]
   TRITON_API_KEYS=["your-strong-triton-key"]
   ```

2. **IP Whitelisting**: Configure your firewall or Nginx to restrict access by IP
   ```
   # In nginx config:
   allow 10.1.1.0/24;  # Your client's IP range
   deny all;  # Deny all other IPs
   ```

3. **SSL**: Always use HTTPS in production

4. **Regular Updates**: Keep all components updated
   ```bash
   docker-compose pull  # Update images
   docker-compose up -d # Restart with updates
   ```

## Monitoring

1. **Health Check**: The service exposes a health endpoint at `/api/health`
2. **Logs**: Check logs with `docker-compose logs -f api`
3. **Metrics**: Monitor system resources with your preferred monitoring tool

## Troubleshooting

1. **Service not starting**: Check logs with `docker-compose logs api`
2. **Connection issues**: Verify firewall rules and network configuration
3. **SSL errors**: Ensure certificates are valid and properly configured

## Support

For additional support, please contact the development team at support@example.com 