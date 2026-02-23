import asyncio
from a2a_sdk.cards import AgentCard
from a2a_sdk.clients import ClientFactory, ClientConfig
from a2a_sdk.transports.base import TransportProtocol
from a2a_sdk.messages import Message
import httpx

class MockTransport(httpx.AsyncTransport):
    async def handle_async_request(self, request):
        print(f"URL: {request.url}")
        print(f"METHOD: {request.method}")
        print(f"HEADERS: {request.headers}")
        content = await request.aread()
        print(f"CONTENT: {content.decode('utf-8')}")
        return httpx.Response(200, content=b'{"choices": [{"message": {"role": "model", "parts": [{"text":"mock"}]}}]}')

async def main():
    agent_card = AgentCard(
        name="test_agent",
        url="https://us-central1-aiplatform.googleapis.com/v1beta1/projects/496235138247/locations/us-central1/reasoningEngines/6148129273430409216/a2a",
        preferred_transport=TransportProtocol.http_json
    )
    
    config = ClientConfig(
        supported_transports=[TransportProtocol.http_json],
        use_client_preference=True,
        httpx_client=httpx.AsyncClient(
            transport=MockTransport(),
            headers={"Authorization": "Bearer fake_token"}
        )
    )
    
    factory = ClientFactory(config)
    client = factory.create(agent_card)
    
    response = client.send_message(Message(role="user", parts=[{"text": "hello"}]))
    try:
        async for chunk in response:
            pass
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
