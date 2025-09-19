# vCon Server Load Test Application

A comprehensive load testing tool for the vCon Server that validates the complete processing pipeline including tagging, file storage, and webhook delivery.

## Features

- **Automated Configuration**: Sets up conserver with ingress lists, tagging, and webhook endpoints
- **JLINC Tracer Support**: Optional integration with JLINC tracing system for event tracking
- **Environment Variable Configuration**: Secure configuration using .env files for sensitive data
- **Load Testing**: Configurable rate, amount, and duration testing
- **Validation**: Validates vCon processing, file saving, and webhook delivery
- **Performance Metrics**: Measures response times, success rates, and throughput
- **Rich CLI**: Beautiful command-line interface with progress bars and results tables

## Installation

### Prerequisites

- Python 3.12+
- uv package manager
- vCon Server running and accessible
- Sample vCon files (you'll need to provide your own)

### Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment variables (optional but recommended):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env
```

3. Make sure your vCon Server is running and accessible

4. Ensure you have sample vCon files available for testing (you'll need to provide your own)

5. (Optional) Start the standalone webhook server for testing:
```bash
uv run test_webhook.py
```

## Usage

### Basic Usage

```bash
# Run with default settings (10 req/s, 100 requests, 60s duration)
uv run load_test_app.py

# Custom configuration
uv run load_test_app.py --rate 20 --amount 200 --duration 120

# Custom conserver URL and token
uv run load_test_app.py --conserver-url http://localhost:8000 --conserver-token your-token
```

### Command Line Options

#### Basic Options
- `--conserver-url`: vCon Server URL (default: http://localhost:8000)
- `--conserver-token`: API token for authentication (default: test-token)
- `--test-directory`: Directory to save test results (default: ./test_output)
- `--webhook-port`: Port for webhook server (default: 8080)
- `--rate`: Requests per second (default: 10)
- `--amount`: Total number of requests (default: 100)
- `--duration`: Test duration in seconds (default: 60)
- `--sample-vcon-path`: Path to sample vCon files (default: ./sample_data)

#### JLINC Tracer Options
- `--jlinc-enabled`: Enable JLINC tracer (flag)
- `--jlinc-data-store-api-url`: JLINC data store API URL
- `--jlinc-data-store-api-key`: JLINC data store API key
- `--jlinc-archive-api-url`: JLINC archive API URL
- `--jlinc-archive-api-key`: JLINC archive API key
- `--jlinc-system-prefix`: JLINC system prefix (default: VCONTest)
- `--jlinc-agreement-id`: JLINC agreement ID
- `--jlinc-hash-event-data/--no-jlinc-hash-event-data`: Hash event data in JLINC
- `--jlinc-dlq-vcon-on-error/--no-jlinc-dlq-vcon-on-error`: Send vCon to DLQ on error

#### Configuration Management Options
- `--restore-config/--no-restore-config`: Restore original conserver configuration after test (default: true)

### Example Commands

```bash
# High load test
uv run load_test_app.py --rate 50 --amount 1000 --duration 300

# Quick validation test
uv run load_test_app.py --rate 5 --amount 10 --duration 30

# Custom test directory
uv run load_test_app.py --test-directory /tmp/vcon_test_output

# Enable JLINC tracer
uv run load_test_app.py --jlinc-enabled --jlinc-data-store-api-key your-key

# Using environment variables (recommended for production)
# Set JLINC_ENABLED=true in .env file, then run:
uv run load_test_app.py

# Skip configuration restoration (keep test config)
uv run load_test_app.py --no-restore-config
```

## Configuration Management

The application automatically handles conserver configuration to ensure your original setup is preserved:

### Automatic Backup and Restore

1. **Backup**: Before applying the test configuration, the application automatically backs up the existing conserver configuration to a timestamped file in the test directory
2. **Test Configuration**: Applies the load test configuration with tagging, webhook, and optional JLINC tracer
3. **Restore**: After the test completes, automatically restores the original configuration (unless disabled with `--no-restore-config`)

### Backup Files

Backup files are saved as `conserver_config_backup_{timestamp}.yml` in the test directory. These files contain the complete original configuration and can be used to manually restore the conserver if needed.

### Manual Configuration Management

```bash
# Run test without restoring original configuration
uv run load_test_app.py --no-restore-config

# The backup file will still be created for manual restoration if needed
```

## Environment Variables

The application supports configuration via environment variables for secure handling of sensitive data like API keys. Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### Available Environment Variables

- `CONSERVER_URL`: vCon Server URL
- `CONSERVER_TOKEN`: API token for authentication
- `JLINC_ENABLED`: Enable JLINC tracer (true/false)
- `JLINC_DATA_STORE_API_URL`: JLINC data store API URL
- `JLINC_DATA_STORE_API_KEY`: JLINC data store API key
- `JLINC_ARCHIVE_API_URL`: JLINC archive API URL
- `JLINC_ARCHIVE_API_KEY`: JLINC archive API key
- `JLINC_SYSTEM_PREFIX`: JLINC system prefix
- `JLINC_AGREEMENT_ID`: JLINC agreement ID
- `JLINC_HASH_EVENT_DATA`: Hash event data in JLINC (true/false)
- `JLINC_DLQ_VCON_ON_ERROR`: Send vCon to DLQ on error (true/false)

## JLINC Tracer Integration

The JLINC tracer provides event tracking and audit capabilities for vCon processing. When enabled, it will:

- Track all vCon processing events
- Store event data in the configured JLINC data store
- Archive processed vCons for compliance
- Handle error scenarios with DLQ (Dead Letter Queue)

### Enabling JLINC Tracer

1. Set up your JLINC server and obtain API keys
2. Configure the environment variables in your `.env` file
3. Run the load test with JLINC enabled:

```bash
# Using environment variables (recommended)
export JLINC_ENABLED=true
uv run load_test_app.py

# Or using command line flags
uv run load_test_app.py --jlinc-enabled --jlinc-data-store-api-key your-key
```

### JLINC Server Requirements

The JLINC tracer requires a running JLINC server accessible at the configured URL (default: `http://jlinc-server:9090`). 

**Example API Keys** (from the provided configuration):
- Data Store API Key: `ZDU5ZWIxMzc0ZDhjOThlNTRkNTYxYzc1Y`
- Archive API Key: `NTFhZGRjNzA0MjFlY2ZiYmFiMGU3MjQ2M`

**Note**: If the JLINC server is not accessible, the tracer will report invalid API keys. Ensure your JLINC server is running and accessible before enabling the tracer.

## How It Works

1. **Configuration Setup**: Creates a conserver configuration with:
   - Ingress list for receiving vCons
   - Random tag addition module
   - File storage for saving processed vCons
   - Webhook endpoint for delivery confirmation
   - Optional JLINC tracer for event tracking

2. **Load Testing**: 
   - Loads a random sample vCon
   - Sends vCons at specified rate to conserver
   - Measures response times and success rates
   - Tracks webhook deliveries and file saves

3. **Validation**:
   - Verifies vCon processing success
   - Confirms webhook delivery
   - Validates file storage
   - Calculates performance metrics

4. **Results**:
   - Displays comprehensive results table
   - Saves detailed JSON report
   - Provides success/failure indicators

## Test Results

The application provides detailed metrics including:

- **Request Metrics**: Total, successful, and failed requests
- **Performance**: Average response time and throughput
- **Delivery**: Webhook delivery rate and file save rate
- **Overall Success**: Pass/fail based on success thresholds

## Output Files

- **Test Results**: JSON file with complete test data saved to the specified test directory
- **Configuration**: YAML configuration used for conserver setup
- **Processed vCons**: Saved vCon files in the test directory

## Requirements

- vCon Server must be running and accessible
- API token must be valid
- Sample vCon files must be available
- Webhook port must be available for the test server

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check that vCon Server is running and accessible
2. **Authentication Failed**: Verify API token is correct
3. **No Sample vCons**: Ensure sample vCon files exist in the specified directory (you'll need to provide your own)
4. **Port Already in Use**: Change webhook port if 8080 is occupied

### Debug Mode

Enable debug logging by setting the log level:
```bash
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" load_test_app.py
```

## Development

### Project Structure

```
load_test/
├── load_test_app.py      # Main application
├── demo.py              # Demo script
├── test_setup.py        # Setup verification script
├── test_webhook.py      # Standalone webhook server for testing
├── pyproject.toml        # Dependencies and configuration
├── .env.example          # Example environment configuration
├── LICENSE              # MIT License
├── CONTRIBUTING.md      # Contribution guidelines
├── README.md            # This file
├── QUICK_REFERENCE.md   # Quick start guide
├── LOAD_TEST_SUMMARY.md # Test results summary
├── PROGRESS_REPORT.md   # Development progress report
├── example_test_config.yml # Example test configuration
```

### Standalone Webhook Server

The repository includes a standalone webhook server (`test_webhook.py`) for testing webhook functionality independently:

```bash
# Start the webhook server
uv run test_webhook.py

# Test webhook endpoint
curl -X POST http://localhost:8080/webhook \
  -H 'Content-Type: application/json' \
  -d '{"test": "data"}'

# Check received webhooks
curl http://localhost:8080/webhooks
```

### Adding Features

The application is modular and can be extended with:
- Additional validation checks
- Custom load testing patterns
- Different storage backends
- Enhanced reporting formats

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.

## Related Projects

This project is part of the vCon ecosystem. For more information about vCon Server, visit the [vCon Server repository](https://github.com/vcon-dev/vcon-server).
