# vCon Server Load Test Application

A comprehensive load testing tool for the vCon Server that validates the complete processing pipeline including tagging, file storage, and webhook delivery.

## Features

- **Automated Configuration**: Sets up conserver with ingress lists, tagging, and webhook endpoints
- **Load Testing**: Configurable rate, amount, and duration testing
- **Validation**: Validates vCon processing, file saving, and webhook delivery
- **Performance Metrics**: Measures response times, success rates, and throughput
- **Rich CLI**: Beautiful command-line interface with progress bars and results tables

## Installation

### Prerequisites

- Python 3.12+
- uv package manager
- vCon Server running and accessible
- Sample vCon files in `./sample_vcons/` directory

### Setup

1. Install dependencies:
```bash
uv sync
```

2. Make sure your vCon Server is running and accessible

3. Ensure sample vCon files are available in the `./sample_vcons/` directory

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

- `--conserver-url`: vCon Server URL (default: http://localhost:8000)
- `--conserver-token`: API token for authentication (default: test-token)
- `--test-directory`: Directory to save test results (default: ./test_results)
- `--webhook-port`: Port for webhook server (default: 8080)
- `--rate`: Requests per second (default: 10)
- `--amount`: Total number of requests (default: 100)
- `--duration`: Test duration in seconds (default: 60)
- `--sample-vcon-path`: Path to sample vCon files (default: ./sample_vcons)

### Example Commands

```bash
# High load test
uv run load_test_app.py --rate 50 --amount 1000 --duration 300

# Quick validation test
uv run load_test_app.py --rate 5 --amount 10 --duration 30

# Custom test directory
uv run load_test_app.py --test-directory /tmp/vcon_test_results
```

## How It Works

1. **Configuration Setup**: Creates a conserver configuration with:
   - Ingress list for receiving vCons
   - Random tag addition module
   - File storage for saving processed vCons
   - Webhook endpoint for delivery confirmation

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

- **Test Results**: JSON file with complete test data saved to `test_results/`
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
3. **No Sample vCons**: Ensure sample vCon files exist in the specified directory
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
├── pyproject.toml        # Dependencies and configuration
├── README.md            # This file
├── sample_vcons/        # Sample vCon files
└── test_results/        # Test output directory
```

### Adding Features

The application is modular and can be extended with:
- Additional validation checks
- Custom load testing patterns
- Different storage backends
- Enhanced reporting formats

## License

This project is part of the vCon ecosystem and follows the same licensing terms.
