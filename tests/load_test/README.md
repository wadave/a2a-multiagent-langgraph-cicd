# Comprehensive Load Testing for A2A Multi-Agent System (adk-mb)

This directory provides comprehensive load testing for the A2A multi-agent system with memory bank integration.

## Overview

The load tests simulate realistic user interactions with the hosting agent, including:
- Weather queries routed to Weather Agent
- Cocktail queries routed to Cocktail Agent
- Multi-agent queries requiring coordination
- General conversation queries
- Mixed realistic conversation patterns

## Prerequisites

1. **Deployed Hosting Agent**: Ensure the hosting agent is deployed to Vertex AI Agent Engine
2. **Environment Variables**: Set the following variables:
   ```bash
   export PROJECT_ID="your-project-id"
   export PROJECT_NUMBER="your-project-number"
   export GOOGLE_CLOUD_REGION="us-central1"
   export AGENT_ENGINE_ID="your-hosting-agent-id"
   ```

3. **Locust Installation**:
   ```bash
   python3 -m venv .locust_env
   source .locust_env/bin/activate
   pip install locust==2.31.1
   ```

## Running Load Tests

### Basic Load Test

Test with the original load_test.py (requires deployment_metadata.json):

```bash
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
locust -f tests/load_test/load_test.py \
  --headless \
  -t 30s -u 5 -r 2 \
  --csv=tests/load_test/.results/results \
  --html=tests/load_test/.results/report.html
```

### Comprehensive Load Test

Test with comprehensive scenarios:

```bash
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
export PROJECT_ID="dw-genai-dev"
export PROJECT_NUMBER="496235138247"
export AGENT_ENGINE_ID="7540524410566868992"

locust -f tests/load_test/load_test_comprehensive.py \
  --headless \
  -t 60s -u 10 -r 2 \
  --csv=tests/load_test/.results/comprehensive_results \
  --html=tests/load_test/.results/comprehensive_report.html
```

### Load Test Scenarios

The comprehensive load test includes:

1. **HostingAgentUser** (Default):
   - 3x weight: Weather queries
   - 3x weight: Cocktail queries
   - 2x weight: Multi-agent queries
   - 1x weight: General queries

2. **MixedLoadUser**:
   - Realistic conversation patterns
   - Progressive query complexity
   - Session continuity

### Command Options

- `-t`: Test duration (e.g., `60s`, `5m`)
- `-u`: Maximum number of concurrent users
- `-r`: User spawn rate per second
- `--headless`: Run without Web UI
- `--csv`: Save results as CSV
- `--html`: Generate HTML report

## Load Test Examples

### Light Load (5 concurrent users, 30 seconds)
```bash
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 30s -u 5 -r 1 \
  --csv=.results/light --html=.results/light.html
```

### Medium Load (20 concurrent users, 2 minutes)
```bash
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 2m -u 20 -r 2 \
  --csv=.results/medium --html=.results/medium.html
```

### Heavy Load (50 concurrent users, 5 minutes)
```bash
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 5m -u 50 -r 5 \
  --csv=.results/heavy --html=.results/heavy.html
```

### Interactive Mode (with Web UI)
```bash
locust -f tests/load_test/load_test_comprehensive.py
# Then open http://localhost:8089 in browser
```

## Monitoring Results

### During Test
- Watch the console output for real-time statistics
- Check for error messages and rate limiting warnings

### After Test
- Open the HTML report: `.results/comprehensive_report.html`
- Review CSV files for detailed metrics:
  - `_stats.csv`: Request statistics
  - `_failures.csv`: Failed requests
  - `_exceptions.csv`: Exceptions encountered

## Key Metrics to Monitor

1. **Response Time**:
   - Median response time
   - 95th percentile
   - 99th percentile

2. **Request Rate**:
   - Requests per second (RPS)
   - Success rate
   - Failure rate

3. **Error Analysis**:
   - Error types
   - Error frequency
   - Rate limiting occurrences

4. **Category Performance**:
   - Weather queries
   - Cocktail queries
   - Multi-agent queries
   - General queries

## Troubleshooting

### Authentication Errors
```bash
# Refresh auth token
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
```

### Rate Limiting (429 errors)
- Reduce concurrent users (`-u`)
- Reduce spawn rate (`-r`)
- Increase wait time between tasks

### Agent Not Found
```bash
# Verify agent deployment
gcloud ai reasoning-engines list \
  --region=us-central1 \
  --project=dw-genai-dev

# Update AGENT_ENGINE_ID
export AGENT_ENGINE_ID="your-correct-id"
```

### Connection Timeouts
- Increase Locust timeout settings
- Check network connectivity
- Verify agent health

## Best Practices

1. **Start Small**: Begin with light load and gradually increase
2. **Monitor Costs**: Load testing can incur significant API costs
3. **Test During Off-Peak**: Avoid impacting production users
4. **Set Duration Limits**: Use `-t` to prevent runaway tests
5. **Analyze Results**: Review HTML reports after each test
6. **Track Baselines**: Compare results across test runs

## Cost Considerations

Load testing the A2A multi-agent system involves:
- Vertex AI Agent Engine API calls
- Gemini model invocations
- MCP server invocations
- Memory Bank operations

**Recommendation**: Run short tests (30-60s) initially and monitor costs before scaling up.

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
- name: Run Load Test
  run: |
    export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
    locust -f tests/load_test/load_test_comprehensive.py \
      --headless -t 30s -u 5 -r 1 \
      --csv=load_test_results --html=load_test_report.html

- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: load-test-results
    path: load_test_*
```

## Support

For issues or questions:
- Check logs in Cloud Console: Vertex AI > Agent Builder > Agents
- Review load test output: `.results/*.html`
- Consult documentation in project README.md
