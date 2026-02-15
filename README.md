# A2A Multi-Agent on Agent Engine

> **⚠️ DISCLAIMER**: THIS DEMO IS INTENDED FOR DEMONSTRATION PURPOSES ONLY. IT IS NOT INTENDED FOR USE IN A PRODUCTION ENVIRONMENT.
>
> **⚠️ Important**: A2A is a work in progress (WIP) thus, in the near future there might be changes that are different from what demonstrated here.

 > **⚠️ Important**: Please run it in **Cloud Shell** to ensure you have the proper permissions.

This document describes a multi-agent set up using Agent2Agent (A2A), LangGraph, Agent Engine, MCP servers, and the LangGraph extension for A2A. It provides an overview of how the A2A protocol works between agents, and how the extension is activated on the server and included in the response.

## Overview

This document describes a web application demonstrating the integration of Google's Open Source frameworks Agent2Agent (A2A) and LangGraph for multi-agent orchestration with Model Context Protocol (MCP) clients. The application features a host agent coordinating tasks between specialized remote A2A agents that interact with various MCP servers to fulfill user requests.

### Architecture

The application utilizes a multi-agent architecture where a host agent delegates tasks to remote A2A agents (Cocktail and Weather) based on the user's query. These agents then interact with corresponding remote MCP servers.

**Host Agent is built using A2A Server.**

![architecture](asset/a2a_langgraph_diagram.png)



### Application Screenshot

![screenshot](asset/screenshot.png)

## Core Components

### Agents

The application employs three distinct agents:

- **Host Agent:** The main entry point that receives user queries, determines the required task(s), and delegates to the appropriate specialized agent(s).
- **Cocktail Agent:** Handles requests related to cocktail recipes and ingredients by interacting with the Cocktail MCP server.
- **Weather Agent:** Manages requests related to weather forecasts by interacting with the Weather MCP servers.

### MCP Servers and Tools

The agents interact with the following MCP servers:

1.  **Cocktail MCP Server** (Local Code)
    - Provides 5 tools:
        - `search cocktail by name`
        - `list all cocktail by first letter`
        - `search ingredient by name`
        - `list random cocktails`
        - `lookup full cocktail details by id`
2.  **Weather MCP Server** (Local Code)
    - Provides 3 tools:
        - `get weather forecast by city name`
        - `get weather forecast by coordinates`
        - `get weather alert by state code`

## Example Usage

Here are some example questions you can ask the chatbot:

- `Please get cocktail margarita id and then full detail of cocktail margarita`
- `Please list a random cocktail`
- `Please get weather forecast for New York`
- `Please get weather forecast for 40.7128,-74.0060`

## Setup and Deployment

### Prerequisites

Before running the application locally, ensure you have the following installed:

1.  [Python 3.12+](https://www.python.org/downloads/)
2.  gcloud SDK: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
3.  **(Optional) uv:** The Python package management tool used in this project. Follow the installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

### 1. Project Structure

Ensure your project follows this structure:

```bash
.
├── .github
│   └── workflows
│       └── deploy.yml      # CI/CD pipeline definition
├── deployment
│   ├── deploy_agents.py    # Script to deploy agents to Vertex AI Agent Engine
│   └── terraform/          # Terraform configuration for infrastructure
├── src
│   ├── a2a_agents/         # Agent definitions (Cocktail, Weather, Hosting)
│   ├── frontend/           # Streamlit/Gradio frontend application
│   └── mcp_servers/        # MCP Server implementations (Cocktail, Weather)
├── dev_notebooks/          # Jupyter notebooks for development/testing
├── asset/
│   ├── a2a_langgraph_diagram.png
│   └── screenshot.png
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock
```

## Deployment

### CI/CD Pipeline

This project uses **GitHub Actions** for continuous integration and deployment. The workflow is defined in `.github/workflows/deploy.yml` and triggers on pushes to the following branches:

-   `staging`: Deploys to the staging environment (Project: `dw-genai-dev`).
-   `main`: Deploys to the production environment (Project: `dw-genai-prod`).

The pipeline performs the following steps:
1.  **Detect Changes**: Identifies which components (MCP servers, agents, frontend, infrastructure) have changed.
2.  **Deploy MCP Servers**: Builds and deploys the Cocktail and Weather MCP servers to Cloud Run.
3.  **Deploy Agents**: Uses `deployment/deploy_agents.py` to deploy the A2A agents (Hosting, Cocktail, Weather) to Vertex AI Agent Engine.
4.  **Deploy Frontend**: Builds and deploys the frontend application to Cloud Run.
5.  **Apply Terraform**: Updates the infrastructure configuration using Terraform.

### Manual Deployment / Local Development

To manually deploy the application or set it up for development, follow these steps:

1.  **Prerequisites**:
    *   [Python 3.12+](https://www.python.org/downloads/)
    *   [gcloud SDK](https://cloud.google.com/sdk/docs/install)
    *   [uv](https://docs.astral.sh/uv/getting-started/installation/) (Recommended package manager)

2.  **Environment Setup**:
    *   Authenticate with Google Cloud:
        ```bash
        gcloud auth login
        gcloud auth application-default login
        gcloud config set project YOUR_PROJECT_ID
        ```
    *   Install dependencies using `uv`:
        ```bash
        uv sync
        ```

3.  **Deploy Components**:
    You can mimic the CI/CD steps locally:

    *   **MCP Servers**:
        ```bash
        gcloud builds submit ./src/mcp_servers/cocktail_mcp_server --tag gcr.io/YOUR_PROJECT_ID/cocktail-remote-mcp-server-lg
        gcloud builds submit ./src/mcp_servers/weather_mcp_server --tag gcr.io/YOUR_PROJECT_ID/weather-remote-mcp-server-lg
        ```

    *   **A2A Agents**:
        Set the required environment variables:
        ```bash
        export PROJECT_ID=YOUR_PROJECT_ID
        export PROJECT_NUMBER=YOUR_PROJECT_NUMBER
        export GOOGLE_CLOUD_REGION=us-central1
        # URLs of the deployed MCP servers from the previous step
        export CT_MCP_SERVER_URL=https://...
        export WEA_MCP_SERVER_URL=https://...
        ```
        Run the deployment script:
        ```bash
        python deployment/deploy_agents.py
        ```

    *   **Frontend**:
        ```bash
        gcloud builds submit ./src/frontend --tag gcr.io/YOUR_PROJECT_ID/a2a-frontend
        ```

### Development Notebooks
For interactive development and testing of individual agents, you can refer to the notebooks in the `dev_notebooks/` directory.

## Disclaimer

**Important**: The sample code provided is for demonstration purposes and illustrates the mechanics of the Agent-to-Agent (A2A) protocol. When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity.

All data received from an external agent—including but not limited to its AgentCard, messages, artifacts, and task statuses—should be handled as untrusted input. For example, a malicious agent could provide an AgentCard containing crafted data in its fields (e.g., description, name, skills.description). If this data is used without sanitization to construct prompts for a Large Language Model (LLM), it could expose your application to prompt injection attacks. Failure to properly validate and sanitize this data before use can introduce security vulnerabilities into your application.

Developers are responsible for implementing appropriate security measures, such as input validation and secure handling of credentials to protect their systems and users.

## License

This project is licensed under the [License](LICENSE).