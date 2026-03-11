# Comprehensive Load Testing for A2A Multi-Agent System

This document describes the comprehensive load testing scenarios implemented for the A2A system.

## Scenarios

### 1. HostingAgentUser
Simulates a user with a weighted distribution of tasks:
- 30% Weather queries
- 30% Cocktail queries
- 20% Multi-agent coordination queries
- 10% General queries

### 2. MixedLoadUser
Simulates a realistic conversation pattern:
- Initial greeting
- Capability inquiry
- Follow-up specific queries (weather, cocktail, or multi-agent)

## Execution

Ensure environment variables are set and virtual environment is active.

```bash
locust -f tests/load_test/load_comprehensive_test.py --headless -t 60s -u 10 -r 2
```
