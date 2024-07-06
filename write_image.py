import threading
import time
import socketio
import base64
import requests
import struct
import numpy
from PIL import Image

client = socketio.Client()

omcb_map = requests.get("https://onemillioncheckboxes.com/api/initial-state")
omcb_map = omcb_map.json()['full_state']
omcb_map = base64.b64decode(omcb_map.encode() + b"=")
num = 0

#image = Image.frombytes("1", (1000, 1000), decode)
#image.save("omcb.png")

target_image = Image.open("target.png")
target_image.thumbnail((300, 300))
target_image = target_image.convert('1')
target_image = numpy.array(target_image)
target_location = (500, 40)

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
    local_map = bin(int.from_bytes(omcb_map, byteorder='big'))
    local_map = list(local_map)
    if "b" in local_map:
        local_map = local_map[2:]
    if bit_queue != []:
        done = False
        while not done:
            if not (local_map[bit_queue[0].idx] != "0") == target_image[bit_queue[0].y][bit_queue[0].x]:
                print(len(bit_queue))
                client.emit('toggle_bit', {'index': bit_queue[0].idx})
                done = True
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

class bit_flip:
    def __init__(self, x, y, idx): # i dont wanna use a tuple thats scaryyyy
        self.x = x
        self.y = y
        self.idx = idx

def toggler():
    global omcb_map
    global bit_queue
    while True:
        if bit_queue == []:
            print("renewing queue")
            local_map = bin(int.from_bytes(omcb_map, byteorder='big'))
            local_map = list(local_map)
            if "b" in local_map:
                local_map = local_map[2:]
            #for i in range(200000, 1000000):
            #    if i % 2:
            #        if local_map[i] == "0":
            #            bit_queue.append(i)
            #    else:
            #        if local_map[i] == "1":
            #            bit_queue.append(i)
            #target image
            #target_location
            for y, y1 in enumerate(target_image):
                for x, x1 in enumerate(y1):
                    if (local_map[((y+target_location[1])*1000)+(x+target_location[0])] != "0") != x1:
                        bit_queue.append(bit_flip(x=x,y=y,idx=((y+target_location[1])*1000)+(x+target_location[0])))
            
        time.sleep(0.01)

threading.Thread(target=toggler).start()
client.connect('https://onemillioncheckboxes.com/', transports='websocket')
client.wait()
