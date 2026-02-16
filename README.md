# A2A Multi-Agent on Agent Engine

> **DISCLAIMER**: This demo is intended for demonstration purposes only. It is not intended for use in a production environment.
>
> **Important**: A2A is a work in progress (WIP) — future changes may differ from what is demonstrated here.

> **Important**: Please run it in **Cloud Shell** to ensure you have the proper permissions.

This project demonstrates a multi-agent system using Agent2Agent (A2A), LangGraph, Vertex AI Agent Engine, MCP servers, and a CI/CD pipeline powered by GitHub Actions and Terraform.

## Overview

A web application demonstrating the integration of Google's Agent2Agent (A2A) protocol and LangGraph for multi-agent orchestration with Model Context Protocol (MCP) clients. A host agent coordinates tasks between specialized remote A2A agents that interact with MCP servers to fulfill user requests.

### Architecture

The application utilizes a multi-agent architecture where a host agent delegates tasks to remote A2A agents (Cocktail and Weather) based on the user's query. These agents then interact with corresponding remote MCP servers.

![architecture](asset/a2a_langgraph_diagram.png)

### Application Screenshot

![screenshot](asset/screenshot.png)

## Project Structure

```
.
├── src/
│   ├── a2a_agents/                     # A2A agent implementations
│   │   ├── common/                     # Shared base classes
│   │   ├── cocktail_agent/             # Cocktail specialist agent
│   │   ├── weather_agent/              # Weather specialist agent
│   │   └── hosting_agent/              # Orchestrator agent
│   ├── frontend/                       # Gradio web frontend
│   └── mcp_servers/                    # MCP server implementations
│       ├── cocktail_mcp_server/        # CocktailDB API wrapper
│       └── weather_mcp_server/         # Weather.gov API wrapper
├── deployment/
│   ├── deploy_agents.py                # Agent deployment script
│   └── terraform/                      # Infrastructure as code
├── tests/
│   ├── unit/                           # Unit tests (pytest)
│   ├── integration/                    # Integration tests
│   ├── eval/                           # ADK evaluation cases
│   └── load_test/                      # Load tests (Locust)
├── dev_notebooks/                      # Development & testing notebooks
├── .github/workflows/deploy.yml        # CI/CD pipeline
└── pyproject.toml                      # Project configuration
```

## Core Components

### Agents

| Agent | Role | Description |
|---|---|---|
| **Hosting Agent** | Orchestrator | Receives user queries, determines the required task, and delegates to the appropriate specialist agent via A2A `send_message`. Handles greetings and capability questions directly. |
| **Cocktail Agent** | Specialist | Handles cocktail recipe and ingredient queries using the Cocktail MCP server. |
| **Weather Agent** | Specialist | Handles weather forecast and alert queries using the Weather MCP server. |

### MCP Servers and Tools

**Cocktail MCP Server** — wraps [TheCocktailDB](https://www.thecocktaildb.com/) API:

| Tool | Description |
|---|---|
| `search_cocktail_by_name(name)` | Search cocktails by name |
| `list_cocktails_by_first_letter(letter)` | List cocktails by first letter |
| `search_ingredient_by_name(name)` | Search ingredient details |
| `list_random_cocktails()` | Get a random cocktail |
| `lookup_cocktail_details_by_id(cocktail_id)` | Full cocktail details by ID |

**Weather MCP Server** — wraps [Weather.gov](https://www.weather.gov/) (NOAA) API:

| Tool | Description |
|---|---|
| `get_forecast_by_city(city, state)` | Weather forecast by city and US state |
| `get_forecast(latitude, longitude)` | Weather forecast by coordinates |
| `get_active_alerts_by_state(state)` | Active weather alerts by state code |

## Example Usage

```
Please get cocktail margarita id and then full detail of cocktail margarita
Please list a random cocktail
Please get weather forecast for New York
Please get weather forecast for 40.7128,-74.0060
Are there any weather alerts for Texas?
```

## Setup and Deployment

### Prerequisites

1. [Python 3.12+](https://www.python.org/downloads/)
2. [gcloud SDK](https://cloud.google.com/sdk/docs/install)
3. [uv](https://docs.astral.sh/uv/getting-started/installation/)
4. [Terraform](https://developer.hashicorp.com/terraform/downloads)
5. [GitHub CLI (gh)](https://cli.github.com/)

### CI/CD Pipeline

This project uses **GitHub Actions** for CI/CD with **Terraform** for infrastructure management.

The workflow (`.github/workflows/deploy.yml`) triggers on pushes to:
- `staging` branch — deploys to the staging project
- `main` branch — deploys to the production project

**Pipeline steps** (each runs only when its source files change):

1. **Detect Changes** — uses `dorny/paths-filter` to identify which components changed
2. **Deploy MCP Servers** — builds and deploys Cocktail/Weather MCP servers to Cloud Run
3. **Deploy Agents** — runs `deployment/deploy_agents.py` to deploy A2A agents to Vertex AI Agent Engine
4. **Deploy Frontend** — builds and deploys the Gradio frontend to Cloud Run
5. **Apply Terraform** — updates Cloud Run service configuration and infrastructure

#### Initial CI/CD Setup

1. Authenticate with Google Cloud and GitHub:
    ```bash
    gcloud auth login
    gcloud auth application-default login
    gh auth login
    ```

2. Run the CI/CD setup:
    ```bash
    uv venv && source .venv/bin/activate
    uv pip install agent-starter-pack --extra-index-url https://us-python.pkg.dev/artifact-foundry-prod/ah-3p-staging-python/simple/

    agent-starter-pack setup-cicd \
      --dev-project YOUR_DEV_PROJECT_ID \
      --staging-project YOUR_STAGING_PROJECT_ID \
      --prod-project YOUR_PROD_PROJECT_ID \
      --repository-name YOUR_REPO_NAME \
      --repository-owner YOUR_GITHUB_USERNAME \
      --cicd-runner github_actions
    ```

### Manual Deployment / Local Development

1. Authenticate and set up:
    ```bash
    gcloud auth login
    gcloud auth application-default login
    gcloud config set project YOUR_PROJECT_ID
    uv sync
    ```

2. Deploy MCP Servers:
    ```bash
    gcloud builds submit ./src/mcp_servers/cocktail_mcp_server \
      --tag gcr.io/YOUR_PROJECT_ID/cocktail-remote-mcp-server-lg
    gcloud builds submit ./src/mcp_servers/weather_mcp_server \
      --tag gcr.io/YOUR_PROJECT_ID/weather-remote-mcp-server-lg
    ```

3. Deploy A2A Agents:
    ```bash
    export PROJECT_ID=YOUR_PROJECT_ID
    export PROJECT_NUMBER=YOUR_PROJECT_NUMBER
    export GOOGLE_CLOUD_REGION=us-central1
    export CT_MCP_SERVER_URL=https://cocktail-remote-mcp-server-lg-PROJECT_NUMBER.REGION.run.app/mcp/
    export WEA_MCP_SERVER_URL=https://weather-remote-mcp-server-lg-PROJECT_NUMBER.REGION.run.app/mcp/
    export PYTHONPATH=src

    python deployment/deploy_agents.py
    ```

4. Deploy Frontend:
    ```bash
    gcloud builds submit ./src/frontend \
      --tag gcr.io/YOUR_PROJECT_ID/a2a-frontend-lg
    ```

## Testing

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Unit Tests

Unit tests cover both MCP servers with mocked external dependencies — no running services required.

```bash
pytest tests/unit/ -v
```

### Integration Tests

Integration tests require running MCP server instances. Set the server URLs via environment variables:

```bash
export COCKTAIL_MCP_URL=http://localhost:8080/mcp
export WEATHER_MCP_URL=http://localhost:8080/mcp
pytest -m integration -v
```

### Run All Tests (excluding integration)

```bash
pytest -m "not integration" -v
```

### Evaluation

ADK evaluation cases are in `tests/eval/`. See [`tests/eval/evalsets/README.md`](tests/eval/evalsets/README.md) for details on the 12 evaluation cases covering direct responses, tool use, orchestrator routing, and edge cases.

```bash
adk eval tests/eval/evalsets/basic.evalset.json --config tests/eval/eval_config.json
```

### Load Testing

Load tests use [Locust](https://locust.io/). See [`tests/load_test/README.md`](tests/load_test/README.md) for details.

### Development Notebooks

Interactive development and testing notebooks are in `dev_notebooks/`:
- `deploy_cocktail_langgraph_agent.ipynb` — Deploy cocktail agent
- `deploy_weather_langgraph_agent.ipynb` — Deploy weather agent
- `deploy_langgraph_host_agent.ipynb` — Deploy hosting agent
- `Langgraph+A2A+AE.ipynb` — End-to-end LangGraph + A2A demo

## Disclaimer

**Important**: The sample code provided is for demonstration purposes and illustrates the mechanics of the Agent-to-Agent (A2A) protocol. When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity.

All data received from an external agent — including but not limited to its AgentCard, messages, artifacts, and task statuses — should be handled as untrusted input. Developers are responsible for implementing appropriate security measures, such as input validation and secure handling of credentials to protect their systems and users.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
