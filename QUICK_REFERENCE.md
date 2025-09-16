# vCon Load Test - Quick Reference Guide

## 🚀 **Quick Start**

### Basic Load Test
```bash
uv run load_test_app.py --rate 10 --amount 100
```

### With JLINC Tracer
```bash
export JLINC_ENABLED=true
uv run load_test_app.py --rate 5 --amount 50
```

### Using Environment File
```bash
cp .env.example .env
# Edit .env with your values
uv run load_test_app.py
```

## 🔧 **Key CLI Options**

### Basic Options
- `--rate`: Requests per second (default: 10)
- `--amount`: Total requests (default: 100)
- `--duration`: Test duration in seconds (default: 60)
- `--conserver-url`: vCon Server URL
- `--conserver-token`: API token

### JLINC Options
- `--jlinc-enabled`: Enable JLINC tracer
- `--jlinc-data-store-api-key`: Data store API key
- `--jlinc-archive-api-key`: Archive API key
- `--jlinc-system-prefix`: System prefix (default: VCONTest)

### Configuration Options
- `--restore-config/--no-restore-config`: Restore original config (default: true)

## 🌍 **Environment Variables**

### Required for JLINC
```bash
JLINC_ENABLED=true
JLINC_DATA_STORE_API_KEY=ZDU5ZWIxMzc0ZDhjOThlNTRkNTYxYzc1Y
JLINC_ARCHIVE_API_KEY=NTFhZGRjNzA0MjFlY2ZiYmFiMGU3MjQ2M
```

### Optional
```bash
CONSERVER_URL=http://localhost:8000
CONSERVER_TOKEN=test-token
JLINC_SYSTEM_PREFIX=VCONTest
```

## 📁 **Important Files**

- `load_test_app.py`: Main application
- `.env.example`: Environment configuration template
- `test_results/`: Test outputs and backups
- `README.md`: Full documentation

## 🔍 **Troubleshooting**

### JLINC API Key Issues
- Ensure JLINC server is running at `http://jlinc-server:9090`
- Use correct API keys from `.env.example`
- Check conserver logs for JLINC processing status

### Configuration Issues
- Backup files are saved in `test_results/conserver_config_backup_*.yml`
- Use `--no-restore-config` to keep test configuration
- Check conserver logs for configuration errors

### Performance Issues
- Start with low rate (1-5 req/s) for testing
- Monitor webhook delivery rates
- Check file storage in `test_results/`

## 📊 **Expected Results**

### Success Indicators
- ✅ Success Rate: 100%
- ✅ Webhook Delivery Rate: >80%
- ✅ File Save Rate: 100%
- ✅ JLINC Events: Processed successfully

### Sample Output
```
Load Test Results
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric                ┃ Value    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Total Requests        │ 100      │
│ Successful Requests   │ 100      │
│ Success Rate          │ 100.00%  │
│ Average Response Time │ 0.034s   │
│ Webhooks Received     │ 100      │
│ Files Saved           │ 100      │
│ Overall Success       │ ✅       │
└───────────────────────┴──────────┘
```

## 🆘 **Emergency Commands**

### Stop Test Early
```bash
Ctrl+C  # Will still run cleanup
```

### Manual Configuration Restore
```bash
# Find backup file
ls test_results/conserver_config_backup_*.yml

# Restore manually (if needed)
curl -X POST http://localhost:8000/config \
  -H "x-conserver-api-token: test-token" \
  -H "Content-Type: application/json" \
  -d @test_results/conserver_config_backup_*.yml
```

### Check System Status
```bash
# Check containers
docker ps

# Check conserver logs
docker logs vcon-server-conserver-1

# Check JLINC server
docker logs vcon-server-jlinc-server-1
```

## 📞 **Support**

- Full documentation: `README.md`
- Progress report: `PROGRESS_REPORT.md`
- Example configuration: `.env.example`
- Test results: `test_results/` directory
