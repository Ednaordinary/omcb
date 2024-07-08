import threading
import time
import socketio
import base64
import requests
import struct
import numpy
import random
from PIL import Image

omcb_map = requests.get("https://onemillioncheckboxes.com/api/initial-state")
omcb_map = omcb_map.json()['full_state']
omcb_map = base64.b64decode(omcb_map.encode() + b"=")
num = 0
flip_count = 0
toggler_on = False

#image = Image.frombytes("1", (1000, 1000), decode)
#image.save("omcb.png")

target_image_list = []
for i in range(1, 47): # frame count
    target_image = Image.open("./frames/" + str(i) + ".png")
    target_image.thumbnail((243, 243))
    target_image = target_image.convert('1')
    #target_image.save("target_factored.png")
    target_image = numpy.array(target_image)
    target_image_list.append(target_image)
target_index = 0
target_location = (480, 30)
target_image2 = Image.open("target2.png")
target_image2.thumbnail((200, 300))
target_image2 = target_image2.convert('1')
target_image2.save("target2_factored.png")
target_image2 = numpy.array(target_image2)
target_location2 = (800, 680)
target_image3 = Image.open("target3.png")
target_image3.thumbnail((90, 700))
target_image3 = target_image2.convert('1')
target_image3.save("target3_factored.png")
target_image3 = numpy.array(target_image3)
target_location3 = (730, 70)

start_time = time.time()
bit_queue = []

def bin_convert(omcb_bin):
    omcb_bin = omcb_bin[omcb_bin.index("b")+1:]
    if len(omcb_bin) < 1000000:
        omcb_bin = ["0"]*(1000000-len(omcb_bin)) + omcb_bin
    return omcb_bin

def set_bit_database(idxs, bit):
    global omcb_map
    omcb_bin = bin(int.from_bytes(omcb_map, byteorder='big'))
    omcb_bin = list(omcb_bin)
    #bin_offset = 2 if "b" in omcb_bin else 0
    omcb_bin = bin_convert(omcb_bin)
    for idx in idxs:
        omcb_bin[idx] = str(bit)
    omcb_bin = ''.join(omcb_bin)
    omcb_map = int(omcb_bin, 2).to_bytes(125000, byteorder='big')

def make_client():
    client = socketio.Client()

    @client.event
    def connect_error(data):
        print("dying:", data)
        
    @client.event
    def disconnect():
        print("dying")
        
    @client.on('batched_bit_toggles')
    def on_batched_bit_toggles(data):
        global omcb_map
        set_bit_database(data[0], 1)
        set_bit_database(data[1], 0)
        global bit_queue
        global flip_count
        local_map = bin(int.from_bytes(omcb_map, byteorder='big'))
        local_map = list(local_map)
        #if "b" in local_map:
        #    local_map = local_map[2:]
        local_map = bin_convert(local_map)
        time.sleep(random.randint(500, 5000)/1000)
        if bit_queue != []:
            #random.shuffle(bit_queue)
            done = 0
            while done < 1:
                # by duplicating the current bit, the clients don't clash into eachother
                try:
                    current_bit = bit_queue[0]
                except: return
                bit_queue.pop(0)
                if current_bit.image == 1:
                    if not (local_map[current_bit.idx] != "0") == target_image[current_bit.y][current_bit.x]:
                        client.emit('toggle_bit', {'index': current_bit.idx})
                        done += 1
                        flip_count +=1
                elif current_bit.image == 2:
                    if not (local_map[current_bit.idx] != "0") == target_image2[current_bit.y][current_bit.x]:
                        client.emit('toggle_bit', {'index': current_bit.idx})
                        done += 1
                        flip_count +=1
                print(len(bit_queue), "|", round(flip_count/(time.time() - start_time), 2), "flips per second", "|", len(omcb_map))

    @client.on('full_state')
    def on_full_state(data):
        global omcb_map
        global num
        print("\nFull state recieved\n")
        #save the state
        omcb_map = base64.b64decode(data['full_state'].encode() + b"=")
        image = Image.frombytes("1", (1000, 1000), omcb_map)
        image.save("./images/" + str(num) + ".png")
        print("\nImage saved\n")
        num += 1

    @client.event
    def connect():
        print("connected")
        pass
    
    return client

class bit_flip:
    def __init__(self, x, y, idx, image): # i dont wanna use a tuple thats scaryyyy
        self.x = x
        self.y = y
        self.idx = idx
        self.image = image

def toggler():
    global omcb_map
    global bit_queue
    global toggler_on
    if not toggler_on:
        toggler_on = True
        print("renewing queue")
        local_map = bin(int.from_bytes(omcb_map, byteorder='big'))
        local_map = list(local_map)
        local_map = bin_convert(local_map)
        for y, y1 in enumerate(target_image):
            for x, x1 in enumerate(y1):
                if (local_map[((y+target_location[1])*1000)+(x+target_location[0])] != "0") != x1:
                    bit_queue.append(bit_flip(x=x,y=y,idx=((y+target_location[1])*1000)+(x+target_location[0]), image=1))
        for y, y1 in enumerate(target_image2):
            for x, x1 in enumerate(y1):
                if (local_map[((y+target_location2[1])*1000)+(x+target_location2[0])] != "0") != x1:
                    bit_queue.append(bit_flip(x=x,y=y,idx=((y+target_location2[1])*1000)+(x+target_location2[0]), image=2))
        for y, y1 in enumerate(target_image3):
            for x, x1 in enumerate(y1):
                if (local_map[((y+target_location3[1])*1000)+(x+target_location3[0])] != "0") != x1:
                    bit_queue.append(bit_flip(x=x,y=y,idx=((y+target_location3[1])*1000)+(x+target_location3[0]), image=2))
        toggler_on = False
        preview_image = numpy.array(Image.frombytes("1", (1000, 1000), omcb_map))
        preview_image2 = numpy.array([[False]*1000]*1000)
        #for bit in bit_queue:
        #    preview_image[(bit.idx // 1000)][bit.idx - ((bit.idx // 1000)*1000)] = True if preview_image[(bit.idx // 1000)][bit.idx - ((bit.idx // 1000)*1000)] != True else False
        #    preview_image2[(bit.idx // 1000)][bit.idx - ((bit.idx // 1000)*1000)] = True
        #preview_image = Image.fromarray((numpy.array(preview_image)*255).round().astype("uint8").squeeze(), mode="L")
        #preview_image.show()
        #preview_image2 = Image.fromarray((numpy.array(preview_image2)*255).round().astype("uint8").squeeze(), mode="L")
        #preview_image2.show()

def renewer():
    global state_setter
    global start_time
    global flip_count
    while True:
        if bit_queue == []:
            print("starting toggler")
            omcb_map_tmp = requests.get("https://onemillioncheckboxes.com/api/initial-state")
            omcb_map_tmp = omcb_map_tmp.json()['full_state']
            omcb_map = base64.b64decode(omcb_map_tmp.encode() + b"=")
            start_time = time.time()
            flip_count = 0
            toggler_thread = threading.Thread(target=toggler)
            toggler_thread.start()
            toggler_thread.join()
        time.sleep(10)

threading.Thread(target=renewer).start()

def run_client(client):
    while True:
        client.connect('https://onemillioncheckboxes.com/', transports='websocket')
        while client.connected:
            print("connection loop")
            time.sleep(5)
            client.wait()
        print("disconnected, restarting in 10")
        time.sleep(10)

client_threads = []
for i in range(1): # be careful, multi client is kinda broken
    client_threads.append(threading.Thread(target=run_client, args=[make_client()]))
for i in client_threads:
    i.start()
    time.sleep(10)
for i in client_threads:
    i.join()
