from enum import Enum

class EventName(Enum):
    Text = "message.text.received"
    Image ="message.image.received"
    Sticker= "message.sticker.received"
    Unsupported = "message.unsupported.received"