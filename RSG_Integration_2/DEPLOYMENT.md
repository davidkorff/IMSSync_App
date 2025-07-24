# RSG Integration Service - Deployment Guide

This application supports two deployment methods:
1. **FastAPI with Uvicorn** (traditional web server)
2. **Azure Functions** (serverless)

Both methods use the exact same business logic and can be used interchangeably.

## Prerequisites

- Python 3.9 or later
- Azure Functions Core Tools (for Azure Functions deployment)
- Azure CLI (for Azure deployment)

## Local Development

### Method 1: FastAPI/Uvicorn (Traditional)

```bash
# Install all dependencies including FastAPI
pip install -r requirements.txt -r requirements-dev.txt

# Copy .env.example to .env and configure
cp .env.example .env

# Run with Python
python main.py

# OR run with Uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the API at: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Method 2: Azure Functions (Serverless)

```bash
# Install core dependencies (no FastAPI needed)
pip install -r requirements.txt

# Copy and configure local settings
cp local.settings.json.template local.settings.json
# Edit local.settings.json with your IMS credentials

# Run with Azure Functions Core Tools
func start
```

Access the API at: http://localhost:7071
- Process transaction: http://localhost:7071/api/triton/transaction/new
- Health check: http://localhost:7071/health

## Testing

The same test scripts work for both deployment methods:

```bash
# These work regardless of which server is running
python test_payload_processing.py TEST.json
python test_full_through_bind.py TEST.json
python test_store_payload.py TEST.json
```

## Production Deployment

### Option 1: Deploy to Azure App Service (FastAPI)

1. Build Docker image:
```bash
docker build -t rsg-integration .
```

2. Deploy to Azure Container Registry:
```bash
az acr build --registry <your-registry> --image rsg-integration .
```

3. Deploy to App Service:
```bash
az webapp create --name <app-name> --plan <plan-name> --deployment-container-image-name <your-registry>.azurecr.io/rsg-integration:latest
```

4. Configure environment variables in App Service settings.

### Option 2: Deploy to Azure Functions

1. Create Function App:
```bash
az functionapp create --name <function-app-name> --storage-account <storage-name> --resource-group <rg-name> --consumption-plan-location <location> --runtime python --runtime-version 3.9 --functions-version 4
```

2. Configure app settings:
```bash
az functionapp config appsettings set --name <function-app-name> --resource-group <rg-name> --settings "IMS_ONE_USERNAME=<username>" "IMS_ONE_PASSWORD=<password>" "IMS_BASE_URL=http://10.64.32.234" "IMS_SERVICES_ENV=/ims_one"
```

3. Deploy the code:
```bash
func azure functionapp publish <function-app-name>
```

## Environment Variables

Both deployment methods use the same environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| IMS_ONE_USERNAME | IMS username | user123 |
| IMS_ONE_PASSWORD | IMS encrypted password | encrypted_string |
| IMS_BASE_URL | IMS base URL | http://10.64.32.234 |
| IMS_SERVICES_ENV | IMS services environment | /ims_one |
| LOG_LEVEL | Logging level | INFO |
| DEBUG | Debug mode | false |

## API Endpoints

Both deployment methods expose the same endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/triton/transaction/new` | POST | Process new transaction |
| `/api/triton/transaction-types` | GET | Get supported transaction types |
| `/api/triton/status` | GET | Triton API status |
| `/api/ims/status` | GET | IMS API status |
| `/health` | GET | Health check |

## Switching Between Deployments

The beauty of this setup is that you can:
- Develop locally with FastAPI for rapid iteration
- Deploy to Azure Functions for production scalability
- Switch between them without code changes
- Use the same tests for both

## Troubleshooting

### FastAPI Issues
- Check that all dev dependencies are installed: `pip install -r requirements-dev.txt`
- Verify .env file exists and has correct values
- Check logs in console output

### Azure Functions Issues
- Ensure Azure Functions Core Tools are installed: `npm install -g azure-functions-core-tools@4`
- Check local.settings.json has all required values
- View logs with: `func start --verbose`
- In Azure: Check Function App logs in Application Insights

### Common Issues
- **Module not found**: Ensure you're in the correct virtual environment
- **IMS connection failed**: Verify IMS credentials and network connectivity
- **Transaction processing fails**: Check that SQL stored procedures are deployed