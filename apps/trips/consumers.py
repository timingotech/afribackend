from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class TripConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for trip updates.

    Connect to: ws://.../ws/trips/<trip_id>/ or /ws/share/<token>/
    """

    async def connect(self):
        # Determine group name from path
        path = self.scope.get('path', '')
        if path.startswith('/ws/trips/'):
            trip_id = path.rstrip('/').split('/')[-1]
            self.group_name = f'trip_{trip_id}'
        elif path.startswith('/ws/share/'):
            token = path.rstrip('/').split('/')[-1]
            self.group_name = f'share_{token}'
        else:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        # Clients may send pings or simple messages; echo back
        typ = content.get('type')
        if typ == 'ping':
            await self.send_json({'type': 'pong'})
        # No other client messages handled here for now

    async def trip.update(self, event):
        # Custom events from server use keys like 'event' and 'data'
        await self.send_json(event.get('data', {}))

    # Generic handler for messages
    async def send_update(self, event):
        await self.send_json(event.get('data', {}))
