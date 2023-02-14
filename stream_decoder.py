import cv2
import urllib.request as ur
import numpy as np
import time

ip_address = "192.168.1.198"
ip_address = "10.0.23.208"
stream = ur.urlopen(
    "http://"
    + ip_address
    + "/api/camera/snapshot?width=640&height=480&quality=60&source=internal&fps=15"
)
bytes = bytes()
idx = 0
stime = time.time()
avg = 0
while True:
    bytes += stream.read(1024)
    elapsed_time = time.time() - stime
    a = bytes.find(b'\xff\xd8')
    b = bytes.find(b'\xff\xd9')
    if a != -1 and b != -1:
        stime = time.time()
        new_avg = avg + (elapsed_time - avg) / (idx + 1)
        print(idx, new_avg, end="\r")
        avg = new_avg
        idx += 1
        jpg = bytes[a:b+2]
        bytes = bytes[b+2:]
        i = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('i', i)
        if cv2.waitKey(1) == 27:
            exit(0)
