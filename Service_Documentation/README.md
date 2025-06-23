# RSG Integration Documentation

Welcome to the comprehensive documentation for the RSG Integration Service. This documentation consolidates all integration requirements, deployment procedures, and technical specifications into a single organized structure.

## Documentation Structure

### 1. [Getting Started](./01_Getting_Started/)
- **[Overview](./01_Getting_Started/01_Overview.md)** - System architecture and key concepts
- **[Quick Start Guide](./01_Getting_Started/02_Quick_Start.md)** - Get up and running quickly
- **[Prerequisites](./01_Getting_Started/03_Prerequisites.md)** - What you need before starting

### 2. [Configuration](./02_Configuration/)
- **[Environment Variables](./02_Configuration/01_Environment_Variables.md)** - Complete .env configuration guide
- **[IMS Settings](./02_Configuration/02_IMS_Settings.md)** - IMS-specific configuration
- **[Source System Settings](./02_Configuration/03_Source_Systems.md)** - Triton, Xuber, and other sources
- **[Security Settings](./02_Configuration/04_Security.md)** - API keys and authentication

### 3. [API Reference](./03_API_Reference/)
- **[Endpoints Overview](./03_API_Reference/01_Endpoints_Overview.md)** - All available endpoints
- **[Transaction Endpoints](./03_API_Reference/02_Transaction_Endpoints.md)** - Transaction submission APIs
- **[Source-Specific Endpoints](./03_API_Reference/03_Source_Specific_Endpoints.md)** - Triton and Xuber endpoints
- **[Authentication](./03_API_Reference/04_Authentication.md)** - API key usage

### 4. [Integration Guides](./04_Integration_Guides/)
- **[Triton Integration](./04_Integration_Guides/01_Triton_Integration.md)** - Complete Triton setup
- **[Xuber Integration](./04_Integration_Guides/02_Xuber_Integration.md)** - Complete Xuber setup
- **[New Program Onboarding](./04_Integration_Guides/03_New_Program_Onboarding.md)** - Adding new sources
- **[Field Mapping Guide](./04_Integration_Guides/04_Field_Mapping.md)** - Data mapping reference

### 5. [Deployment](./05_Deployment/)
- **[Deployment Overview](./05_Deployment/01_Overview.md)** - Deployment options
- **[Docker Deployment](./05_Deployment/02_Docker_Deployment.md)** - Container-based setup
- **[Direct Deployment](./05_Deployment/03_Direct_Deployment.md)** - Python-based setup
- **[Network Requirements](./05_Deployment/04_Network_Requirements.md)** - Firewall and connectivity
- **[Production Checklist](./05_Deployment/05_Production_Checklist.md)** - Pre-launch verification

### 6. [IMS Integration](./06_IMS_Integration/)
- **[IMS Overview](./06_IMS_Integration/01_IMS_Overview.md)** - Understanding IMS
- **[IMS Web Services](./06_IMS_Integration/02_Web_Services.md)** - SOAP API reference
- **[IMS Workflow](./06_IMS_Integration/03_Workflow.md)** - Quote to policy process
- **[IMS Functions Reference](./06_IMS_Integration/04_Functions_Reference.md)** - Detailed function guide

### 7. [Operations](./07_Operations/)
- **[Monitoring](./07_Operations/01_Monitoring.md)** - Health checks and metrics
- **[Logging](./07_Operations/02_Logging.md)** - Log management
- **[Troubleshooting](./07_Operations/03_Troubleshooting.md)** - Common issues and solutions
- **[Maintenance](./07_Operations/04_Maintenance.md)** - Regular maintenance tasks

### 8. [Development](./08_Development/)
- **[Architecture](./08_Development/01_Architecture.md)** - System design
- **[Code Structure](./08_Development/02_Code_Structure.md)** - Project organization
- **[Testing](./08_Development/03_Testing.md)** - Test procedures
- **[Contributing](./08_Development/04_Contributing.md)** - Development guidelines

## Quick Links

- **Need to deploy quickly?** Start with the [Quick Start Guide](./01_Getting_Started/02_Quick_Start.md)
- **Setting up Triton?** See [Triton Integration](./04_Integration_Guides/01_Triton_Integration.md)
- **Configuration issues?** Check [Environment Variables](./02_Configuration/01_Environment_Variables.md)
- **API questions?** Refer to [Endpoints Overview](./03_API_Reference/01_Endpoints_Overview.md)

## Version Information

- **Documentation Version**: 2.0
- **Last Updated**: January 2025
- **API Version**: v1
- **Supported Sources**: Triton, Xuber (extensible to others)

## Support

For support, please contact the RSG Integration team or refer to the [Troubleshooting Guide](./07_Operations/03_Troubleshooting.md).