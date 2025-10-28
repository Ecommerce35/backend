from channels.generic.websocket import AsyncWebsocketConsumer
import json

class VendorOrderConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize group_name to avoid AttributeError
        self.group_name = None 

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or not hasattr(user, 'vendor'):
            await self.close()
            return

        self.vendor_id = user.vendor.id  # Assuming user is linked to a vendor
        self.group_name = f"vendor_{self.vendor_id}"

        # Add vendor to the WebSocket group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Safely remove vendor from WebSocket group only if group_name is set
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_order_notification(self, event):
        # Send new order details to the vendor
        await self.send(text_data=json.dumps(event["message"]))
