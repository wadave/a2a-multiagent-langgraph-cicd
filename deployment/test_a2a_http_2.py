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
    
    message_data = {
        "messageId": "someid",
        "role": "user",
        "parts": [{"kind": "text", "text": "Who is leading the current F1 standings"}],
    }
    
    res = remote_agent.query(class_method="on_message_send", request=message_data, context={})
    print("Response:", res)

if __name__ == "__main__":
    main()
