#!/usr/bin/python3

import time
import signal
import sys

def signal_handler(sig, frame):
    print('olatodos', sig, 'opfl', frame)
    sys.exit(0)
    
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
    
for i in range(500):
    time.sleep(0.010)
    
print('terminado')