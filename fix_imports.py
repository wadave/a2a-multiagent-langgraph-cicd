import os
import glob

base_dir = "/usr/local/google/home/wangdave/remote_ws/projects/a2a-multiagent-langgraph-cicd/src/a2a_agents"

replacements = {
    "from common": "from a2a_agents.common",
    "from cocktail_agent": "from a2a_agents.cocktail_agent",
    "from weather_agent": "from a2a_agents.weather_agent",
    "from hosting_agent": "from a2a_agents.hosting_agent"
}

for filepath in glob.glob(f"{base_dir}/**/*.py", recursive=True):
    with open(filepath, "r") as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
