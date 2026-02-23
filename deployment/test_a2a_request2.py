import asyncio
from a2a_sdk.cards import AgentCard
from a2a_sdk.clients import ClientFactory, ClientConfig
from a2a_sdk.transports.base import TransportProtocol
from a2a_sdk.messages import Message
import httpx

async def main():
    agent_card = AgentCard(
        name="test_agent",
        url="https://us-central1-aiplatform.googleapis.com/v1beta1/projects/496235138247/locations/us-central1/reasoningEngines/6148129273430409216/a2a",
        preferred_transport=TransportProtocol.http_json
    )
    
    # We will let a2a_sdk construct the request with the actual token
    # To do this, we need to supply an actual token via ADC or shell
    import google.auth
    credentials, project = google.auth.default()
    import google.auth.transport.requests
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    config = ClientConfig(
        supported_transports=[TransportProtocol.http_json],
        use_client_preference=True,
        httpx_client=httpx.AsyncClient(
            headers={"Authorization": f"Bearer {credentials.token}"}
        )
    )
    
    factory = ClientFactory(config)
    client = factory.create(agent_card)
    
    # Use valid syntax for parts as per standard Gemini
    response = client.send_message(Message(role="user", parts=["hello"]))
    try:
        async for chunk in response:
            print(f"CHUNK: {chunk}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
