import threading
import time
import socketio
import base64
import requests
import struct
from PIL import Image

client = socketio.Client()

omcb_map = requests.get("https://onemillioncheckboxes.com/api/initial-state")
omcb_map = omcb_map.json()['full_state']
omcb_map = base64.b64decode(omcb_map.encode() + b"=")
num = 0

#image = Image.frombytes("1", (1000, 1000), decode)
#image.save("omcb.png")

bit_queue = []

def set_bit_database(idxs, bit):
    global omcb_map
    omcb_bin = bin(int.from_bytes(omcb_map, byteorder='big'))
    omcb_bin = list(omcb_bin)
    bin_offset = 2 if "b" in omcb_bin else 0
    for idx in idxs:
        try:
            omcb_bin[idx + bin_offset] = str(bit)
        except:
            pass
    omcb_bin = ''.join(omcb_bin)
    omcb_bin = omcb_bin[bin_offset:]
    omcb_map = int(omcb_bin, 2).to_bytes(125000, byteorder='big')

@client.event
def connect_error(data):
    print("dying:", data)
    
@client.event
def disconnect():
    print("dying")
    
@client.on('batched_bit_toggles')
def on_batched_bit_toggles(data):
    set_bit_database(data[0], 1)
    set_bit_database(data[1], 0)
    global bit_queue
    if bit_queue != []:
        print(len(bit_queue))
        client.emit('toggle_bit', {'index': bit_queue[0]})
        bit_queue.pop(0)

@client.on('full_state')
def on_full_state(data):
    global num
    num += 1
    #verify that the old state isn't weird
    global omcb_map
    image = Image.frombytes("1", (1000, 1000), omcb_map)
    image.save("./images/" + str(num) + ".png")
    #save the state
    omcb_map = base64.b64decode(data['full_state'].encode() + b"=")

@client.event
def connect():
    pass

def toggler():
    global omcb_map
    global bit_queue
    while True:
        if bit_queue == []:
            print("renewing queue")
            local_map = bin(int.from_bytes(omcb_map, byteorder='big'))
            for i in range(1000000):
                 if local_map[i] != (0 if i % 2 else 1):
                    bit_queue.append(i)

threading.Thread(target=toggler).start()
client.connect('https://onemillioncheckboxes.com/', transports='websocket')
client.wait()
