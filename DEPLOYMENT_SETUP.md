# IMS Network Deployment Setup

## Prerequisites on IMS Network Computer

1. **Python 3.8+** installed
2. **Git** for cloning the repository
3. **Network access** to IMS SOAP endpoints
4. **MySQL access** to Triton database (via VPN/tunnel if needed)

## Quick Setup Instructions

### 1. Clone and Setup Environment
```bash
# Clone the repository
git clone <your-repo-url>
cd "RSG Integration"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with actual values (see REQUIRED_CONFIG.md)
```

### 3. Test IMS Connectivity
```bash
# Test IMS login
python test_ims_login.py

# Test producer search
python test_producer_search.py
```

### 4. Run Triton to IMS Integration
```bash
# Start the MySQL polling service
python run_mysql_polling.py

# Or run the full API service
python -m app.main
```

## Files to Configure on IMS Network

1. **`.env`** - Environment variables (copy from .env.example)
2. **`IMS_Configs/`** - IMS configuration files (should already exist)
3. **`templates/`** - Excel rater templates (create as needed)

## Testing Components

- `test_ims_login.py` - Test IMS authentication
- `test_producer_search.py` - Test producer lookup
- `test_triton_integration.py` - Test full integration flow
- `run_mysql_polling.py` - Run the polling service standalone

## Key Environment Variables to Set

See `REQUIRED_CONFIG.md` for complete list of required configuration values.