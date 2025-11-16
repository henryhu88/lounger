import asyncio

from lounger.centrifuge.centrifuge_client_factory import create_client, subscribe_to_shop_channel
from lounger.commons.load_config import global_test_config
from lounger.utils.cache import cache


class CentrifugeClientManager:
    """
    Elegant Centrifuge client manager, using singleton pattern to manage client instances.
    Responsible for creating, storing and providing access to Centrifuge clients.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clients = {}
        return cls._instance

    def get_client(self, client_type: str) -> object:
        """Get client instance of specified type"""
        return self._clients.get(client_type.lower())

    def set_client(self, client_type: str, client: object) -> None:
        """Set client instance of specified type"""
        self._clients[client_type.lower()] = client

    def has_clients(self) -> bool:
        """Check if client instances have been created"""
        return len(self._clients) > 0


# Create global client manager instance
client_manager = CentrifugeClientManager()


async def centrifuge_send_message(client, *args, **kwargs):
    """
    Send a text message via RPC.

    :param client: Centrifuge client instance.
    """
    message = kwargs.get('message')
    if not message:
        raise ValueError("Missing required 'message' parameter")

    data = {
        "content": f"<p><span style=\"white-space: pre-wrap;\">{message}</span></p>",
        "message_type": "text",
        "conversation_id": client.conversation_id,
        "shop_id": client.shop_id,
        "receiver_user_ids": [""],
    }
    await client.rpc("send_message", data)
    # Sleep briefly to avoid rate limiting or race conditions
    await asyncio.sleep(1)


def _get_centrifuge_config():
    """Get Centrifuge configuration information, loaded only when needed"""
    url = global_test_config("url")
    return {
        'url': url,
        'shop_id': cache.get('shop_id'),
        'conversation_id': cache.get('conversation_id'),
        'default_headers': cache.get('default_headers'),
        'c_headers': cache.get('c_headers')
    }


def _initialize_clients():
    """
    Initialize B and C end Centrifuge clients
    Called only when clients are first needed, avoiding premature configuration loading
    """
    loop = asyncio.get_event_loop()
    config = _get_centrifuge_config()

    # create C client role
    c_client = create_client(
        'C', config['shop_id'], config['conversation_id'],
        config['url'], config['default_headers'], config['c_headers']
    )

    # create B client role
    b_client = create_client(
        'B', config['shop_id'], config['conversation_id'],
        config['url'], config['default_headers'], config['c_headers']
    )

    # ensure B client uses the same conversation ID as C client
    b_client.conversation_id = c_client.conversation_id

    # subscribe to shop channel
    loop.run_until_complete(subscribe_to_shop_channel(c_client, config['shop_id']))
    loop.run_until_complete(subscribe_to_shop_channel(b_client, config['shop_id']))

    # save client instances
    client_manager.set_client('c', c_client)
    client_manager.set_client('b', b_client)


def send_centrifuge(role, action, *args, **kwargs):
    """
    Public API interface for test scripts to interact with Centrifuge.

    :params type: Client type, 'B' for B-end, 'C' for C-end
    :params function: Operation to perform, supports 'send_message' or 'disconnect'
    """
    client_role = role.upper()
    loop = asyncio.get_event_loop()

    # Check if client instances already exist, initialize if not
    if not client_manager.has_clients():
        _initialize_clients()

    # Get the corresponding client
    client = client_manager.get_client(client_role)

    # Execute the requested operation
    if action == 'send_message':
        loop.run_until_complete(centrifuge_send_message(client, *args, **kwargs))
    elif action == 'disconnect':
        loop.run_until_complete(client.disconnect())
    else:
        raise ValueError(f"Unsupported function: {action}")
