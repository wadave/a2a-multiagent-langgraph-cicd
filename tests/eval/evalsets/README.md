# A2A Multi-Agent Evaluation Sets

Evaluation cases for validating the three-agent system: Hosting (orchestrator), Cocktail, and Weather agents.

## Agents Under Test

### Hosting Agent (Orchestrator)
Routes user queries to the appropriate specialist agent. Responds directly to greetings and capability questions without using tools.

### Cocktail Agent
Uses the Cocktail MCP Server. Available tools:
- `search_cocktail_by_name(name)` - Search cocktails by name
- `list_cocktails_by_first_letter(letter)` - List cocktails by first letter
- `search_ingredient_by_name(name)` - Search ingredient details
- `list_random_cocktails()` - Get a random cocktail
- `lookup_cocktail_details_by_id(cocktail_id)` - Look up cocktail by ID

### Weather Agent
Uses the Weather MCP Server. Available tools:
- `get_forecast_by_city(city, state)` - Weather forecast by city and state
- `get_forecast(latitude, longitude)` - Weather forecast by coordinates
- `get_active_alerts_by_state(state)` - Active weather alerts by state code

## Eval Cases

| eval_id | Category | Expected Behavior |
|---|---|---|
| `greeting_hello` | Direct response | No tools, friendly greeting |
| `capabilities_question` | Direct response | No tools, describe weather + cocktail capabilities |
| `cocktail_search_margarita` | Cocktail tool use | `search_cocktail_by_name` |
| `cocktail_random` | Cocktail tool use | `list_random_cocktails` |
| `cocktail_by_letter` | Cocktail tool use | `list_cocktails_by_first_letter` |
| `ingredient_search` | Cocktail tool use | `search_ingredient_by_name` |
| `weather_forecast_city` | Weather tool use | `get_forecast_by_city` |
| `weather_alerts` | Weather tool use | `get_active_alerts_by_state` |
| `routing_weather` | Orchestrator routing | `send_message` to Weather Agent |
| `routing_cocktail` | Orchestrator routing | `send_message` to Cocktail Agent |
| `nonexistent_cocktail` | Edge case | Graceful "not found" handling |
| `ambiguous_query` | Edge case | Direct response, no crash |

## Evaluation Metrics

Configured in `eval_config.json`:

- **tool_trajectory_avg_score** (threshold: 0.9) - Validates correct tool selection and call order
- **rubric_based_final_response_quality_v1** (threshold: 0.8) - LLM-judged quality across:
  - *relevance* - Response addresses the query
  - *helpfulness* - Response provides useful information
  - *format* - Response uses clear Markdown formatting
  - *tool_routing* - Correct agent/tool is selected

## Running Evaluations

```bash
# Run with ADK eval CLI
adk eval tests/eval/evalsets/basic.evalset.json --config tests/eval/eval_config.json
```

## Adding New Cases

1. Add a new entry to `eval_cases` in `basic.evalset.json`
2. Set `tool_uses` to the expected tool calls (empty array for direct responses)
3. Use `app_name: "a2a-multiagent-adk-memory"` in `session_input`

See [ADK documentation](https://google.github.io/adk-docs/) for advanced evaluation options.
