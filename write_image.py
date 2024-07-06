import threading
import time
import socketio
import base64
import requests
import struct
from PIL import Image

client = socketio.Client()

omcb = requests.get("https://onemillioncheckboxes.com/api/initial-state")
omcb = omcb.json()['full_state']
omcb_map = base64.b64decode(omcb.encode() + b"=")

#image = Image.frombytes("1", (1000, 1000), decode)
#image.save("omcb.png")

def set_bit_database(idx, bit):
    global omcb_map
    byte = bin(int.from_bytes(omcb_map[idx // 8], byteorder='big'))[2:]
    byte[idx] = bit
    omcb_map[idx // 8] = struct.pack("B", int(byte, 2))

@client.event
def connect_error(data):
    print("dying:", data)
    
@client.event
def disconnect():
    print("dying")
    
@client.on('batched_bit_toggles')
def on_batched_bit_toggles(data):
    pass

@client.on('full_state')
def on_full_state(data):
    #verify that the old state isn't weird
    

@client.event
def connect():
    pass
