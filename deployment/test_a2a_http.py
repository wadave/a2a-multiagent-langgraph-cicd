import os
import logging
import httpx
import vertexai

logging.basicConfig(level=logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

def main():
    vertexai.init(project="dw-genai-dev", location="us-central1")
    client = vertexai.Client(
        project="dw-genai-dev",
        location="us-central1",
        http_options={"api_version": "v1beta1"},
    )
    
    remote_agent = client.agent_engines.get(
        name="projects/496235138247/locations/us-central1/reasoningEngines/6148129273430409216",
    )
    
    import asyncio
    
    async def run():
        message_data = {
            "messageId": "someid",
            "role": "user",
            "parts": [{"kind": "text", "text": "Who is leading the current F1 standings"}],
        }
        res = await remote_agent.on_message_send(**message_data)
        print("Response:", res)
        
    asyncio.run(run())

if __name__ == "__main__":
    main()
