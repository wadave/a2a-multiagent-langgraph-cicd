# Testing Summary - A2A Multi-Agent System (adk-mb)

## Overview

This document summarizes all testing capabilities for the A2A multi-agent system with Memory Bank integration.

## Test Structure

```
tests/
├── unit/                           # Unit tests
│   ├── test_agent_cards.py        # Agent card configuration tests (NEW)
│   ├── test_orchestrator_logic.py # Orchestrator logic tests (NEW)
│   ├── test_frontend_logic.py     # Frontend logic tests (NEW)
│   ├── test_cocktail_server.py    # Cocktail MCP server tests (EXISTING)
│   └── test_weather_server.py     # Weather MCP server tests (EXISTING)
├── integration/                    # Integration tests
│   ├── test_cocktail_mcp_server.py
│   ├── test_weather_mcp_server.py
│   ├── test_cocktail_agent_local.py
│   ├── test_cocktail_agent_remote_a2a.py
│   ├── test_hosting_agent_remote.py
│   ├── test_frontend_deployed.py
│   └── manual_test_*.py
├── eval/                          # Evaluation tests
│   ├── test_agent_evaluation.py   # Agent evaluation framework (NEW)
│   ├── run_evaluation.py          # Evaluation runner script (NEW)
│   ├── eval_config.json           # Evaluation criteria (EXISTING)
│   └── evalsets/
│       ├── basic.evalset.json     # Basic test cases (EXISTING)
│       └── comprehensive.evalset.json  # Comprehensive test cases (NEW)
└── load_test/                     # Load/performance tests
    ├── load_test.py               # Basic load test (EXISTING)
    ├── load_test_comprehensive.py # Comprehensive load test (NEW)
    ├── README.md                  # Basic instructions (EXISTING)
    └── README_COMPREHENSIVE.md    # Detailed instructions (NEW)
```

## Test Coverage

### 1. Unit Tests ✅

#### A. Agent Cards Tests (`test_agent_cards.py`) - NEW
**Purpose**: Validate agent card configurations and naming conventions

**Test Classes**:
- `TestCocktailAgentCard`: Cocktail agent card validation
- `TestWeatherAgentCard`: Weather agent card validation
- `TestHostingAgentCard`: Hosting agent card validation
- `TestAgentCardConsistency`: Cross-agent consistency checks

**Coverage**:
- ✓ Agent skill configuration
- ✓ Agent naming (adk-mb convention)
- ✓ Skill examples and tags
- ✓ Description validation
- ✓ Unique skill IDs

**Run Tests**:
```bash
pytest tests/unit/test_agent_cards.py -v
```

#### B. Orchestrator Logic Tests (`test_orchestrator_logic.py`) - NEW
**Purpose**: Test orchestrator agent initialization and coordination logic

**Test Classes**:
- `TestOrchestratorInitialization`: Initialization and client factory
- `TestOrchestratorAgentRegistration`: Agent card registration
- `TestOrchestratorAgentListing`: Listing remote agents
- `TestOrchestratorStateManagement`: State tracking
- `TestOrchestratorAgentCreation`: Agent creation and tools
- `TestOrchestratorInstructionGeneration`: Instruction generation

**Coverage**:
- ✓ Orchestrator initialization
- ✓ Agent card registration
- ✓ Remote agent listing
- ✓ State management
- ✓ Tool configuration
- ✓ Instruction generation

**Run Tests**:
```bash
pytest tests/unit/test_orchestrator_logic.py -v
```

#### C. Frontend Logic Tests (`test_frontend_logic.py`) - NEW
**Purpose**: Test frontend authentication, configuration, and response handling

**Test Classes**:
- `TestGoogleAuthClass`: Google Cloud authentication
- `TestEnvironmentConfiguration`: Environment variable handling
- `TestAgentCardRetrieval`: Agent card fetching
- `TestResponseProcessing`: Message and task processing
- `TestErrorHandling`: Error handling
- `TestResourceNameConstruction`: Resource name formatting

**Coverage**:
- ✓ Google Cloud authentication flow
- ✓ Environment configuration
- ✓ Agent card retrieval
- ✓ Message creation
- ✓ Error handling
- ✓ Resource name formatting

**Run Tests**:
```bash
pytest tests/unit/test_frontend_logic.py -v
```

#### D. MCP Server Tests (EXISTING)
**Files**: `test_cocktail_server.py`, `test_weather_server.py`

**Coverage**:
- ✓ API request handling
- ✓ Response formatting
- ✓ Error handling
- ✓ Data validation
- ✓ Tool function logic

**Run Tests**:
```bash
pytest tests/unit/test_cocktail_server.py -v
pytest tests/unit/test_weather_server.py -v
```

### 2. Integration Tests ✅

**Purpose**: Test end-to-end functionality of deployed components

**Test Files**:
- `test_cocktail_mcp_server.py`: Cocktail MCP server integration
- `test_weather_mcp_server.py`: Weather MCP server integration
- `test_cocktail_agent_local.py`: Local cocktail agent testing
- `test_cocktail_agent_remote_a2a.py`: Remote A2A protocol testing
- `test_hosting_agent_remote.py`: Hosting agent integration
- `test_frontend_deployed.py`: Frontend deployment validation
- `manual_test_*.py`: Manual testing scripts

**Run Tests**:
```bash
# Test MCP servers
python tests/integration/test_cocktail_mcp_server.py
python tests/integration/test_weather_mcp_server.py

# Test agents
python tests/integration/test_cocktail_agent_local.py
python tests/integration/test_hosting_agent_remote.py

# Test frontend
python tests/integration/test_frontend_deployed.py
```

### 3. Evaluation Tests ✅

#### A. Agent Evaluation Framework (`test_agent_evaluation.py`) - NEW
**Purpose**: Evaluate agent performance against quality rubrics

**Test Classes**:
- `TestAgentEvaluation`: Config and evalset validation
- `TestRubricCriteria`: Rubric definitions
- `TestAgentResponseQuality`: Response quality metrics
- `TestMemoryBankIntegration`: Memory functionality
- `TestMultiAgentCoordination`: Multi-agent scenarios

**Rubric Criteria**:
- **Relevance**: Response addresses user query (threshold: 0.8)
- **Helpfulness**: Provides useful information
- **Format**: Markdown formatting
- **Tool Routing**: Correct agent selection

**Run Tests**:
```bash
pytest tests/eval/test_agent_evaluation.py -v
```

#### B. Evaluation Runner (`run_evaluation.py`) - NEW
**Purpose**: Execute evaluation tests against live agents

**Features**:
- Load evaluation sets
- Calculate rubric scores
- Generate evaluation reports
- Track pass/fail rates

**Run Evaluation**:
```bash
python tests/eval/run_evaluation.py \
  --evalset comprehensive \
  --output results/eval_results.json
```

#### C. Evaluation Sets

**Basic Evalset** (existing):
- Greeting and capability queries
- Simple tool routing
- Basic validation

**Comprehensive Evalset** (NEW):
- 14 test cases covering:
  - Weather queries (simple, coordinates, alerts)
  - Cocktail queries (search, random, by letter, ingredient)
  - Multi-agent coordination
  - General conversation
  - Memory continuity
  - Error handling

### 4. Load/Performance Tests ✅

#### A. Basic Load Test (`load_test.py`) - EXISTING
**Purpose**: Basic streaming query load testing

**Features**:
- Stream query simulation
- Rate limit detection
- Error tracking

**Run Test**:
```bash
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
locust -f tests/load_test/load_test.py --headless -t 30s -u 5 -r 2
```

#### B. Comprehensive Load Test (`load_test_comprehensive.py`) - NEW
**Purpose**: Realistic multi-scenario load testing

**User Types**:
- `HostingAgentUser`: Weighted task distribution
  - 3x Weather queries
  - 3x Cocktail queries
  - 2x Multi-agent queries
  - 1x General queries
- `MixedLoadUser`: Realistic conversation patterns

**Test Scenarios**:
```bash
# Light load (5 users, 30s)
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 30s -u 5 -r 1

# Medium load (20 users, 2m)
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 2m -u 20 -r 2

# Heavy load (50 users, 5m)
locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 5m -u 50 -r 5
```

**Metrics Tracked**:
- Response time (median, 95th, 99th percentile)
- Request rate (RPS)
- Success/failure rates
- Category-specific performance

## Running All Tests

### Run All Unit Tests
```bash
pytest tests/unit/ -v --cov=src
```

### Run All Integration Tests
```bash
# Set environment variables first
export PROJECT_ID="dw-genai-dev"
export PROJECT_NUMBER="496235138247"
export GOOGLE_CLOUD_REGION="us-central1"

# Run integration tests
pytest tests/integration/ -v
```

### Run Evaluation Suite
```bash
python tests/eval/run_evaluation.py --evalset comprehensive
```

### Run Load Tests
```bash
export _AUTH_TOKEN=$(gcloud auth print-access-token -q)
export AGENT_ENGINE_ID="your-agent-id"

locust -f tests/load_test/load_test_comprehensive.py \
  --headless -t 60s -u 10 -r 2 \
  --html=load_test_report.html
```

## Test Quality Metrics

### Code Coverage Goals
- Unit Tests: > 80% coverage
- Integration Tests: All critical paths
- Evaluation: All rubric criteria
- Load Tests: All query categories

### Success Criteria
- ✓ All unit tests pass
- ✓ Integration tests complete successfully
- ✓ Evaluation pass rate > 90%
- ✓ Load test median response time < 2s
- ✓ Load test success rate > 95%

## CI/CD Integration

### GitHub Actions Integration
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Run Unit Tests
      run: pytest tests/unit/ -v --cov=src --cov-report=xml

    - name: Run Evaluation Tests
      run: |
        pytest tests/eval/test_agent_evaluation.py -v
        python tests/eval/run_evaluation.py --evalset basic

    - name: Upload Coverage
      uses: codecov/codecov-action@v3
```

## Test Maintenance

### Adding New Tests

1. **Unit Tests**: Add to appropriate test file in `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/`
3. **Evaluation Cases**: Add to evalset JSON in `tests/eval/evalsets/`
4. **Load Scenarios**: Add task to load test user classes

### Updating Tests for Code Changes

When code changes:
1. Update relevant unit tests
2. Update integration tests if APIs changed
3. Add new evaluation cases for new features
4. Update load test queries if needed

## Documentation

- **Unit Tests**: Docstrings in test files
- **Integration Tests**: Comments in test scripts
- **Evaluation**: `tests/eval/README.md`
- **Load Tests**: `tests/load_test/README_COMPREHENSIVE.md`

## Support

For testing issues:
- Check test output and error messages
- Review test documentation
- Consult main README.md
- Check CI/CD pipeline logs

## Summary

**Total Test Coverage**:
- ✅ 3 NEW unit test files (150+ tests)
- ✅ 8 integration test files
- ✅ 1 evaluation framework with 14+ test cases
- ✅ 2 load test implementations
- ✅ Comprehensive documentation

**Status**: Complete and production-ready testing suite
