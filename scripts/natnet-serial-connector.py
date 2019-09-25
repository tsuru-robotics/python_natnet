import natnet
import serial
import signal
import datetime
import threading
import time

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

signal.signal(signal.SIGINT, signal_handler)

oldTimestamp = 0.0
NatNetCoords = [0.0, 0.0, 0.0]
oldNatNetCoords = [0.0, 0.0, 0.0]
NatNetVel = [0.0, 0.0, 0.0]
oldNatNetVel = [0.0, 0.0, 0.0]

def ReadNatnet(rigid_bodies, markers, timing):
    global NatNetCoords, oldNatNetCoords, NatNetVel, oldTimestamp
    if len(rigid_bodies) == 1:
        NatNetCoords[0] = rigid_bodies[0].position[0]
        NatNetCoords[1] = rigid_bodies[0].position[2]
        NatNetCoords[2] = -rigid_bodies[0].position[1]
        dt = timing.timestamp - oldTimestamp
        for i in range(0, 3):
            NatNetVel[i] = (oldNatNetCoords[i] - NatNetCoords[i]) / dt
            NatNetVel[i] = NatNetVel[i] * 0.7 + oldNatNetVel[i] * 0.3
            oldNatNetVel[i] = NatNetVel[i]
            oldNatNetCoords[i] = NatNetCoords[i]
        oldTimestamp = timing.timestamp

# open serial port
ser = serial.Serial('COM9', baudrate = 921600)
# open natnet connection
net = natnet.Client.connect()
net.set_callback(ReadNatnet)
thread = threading.Thread(target=net.spin)
thread.setDaemon = True
thread.start()

filename = datetime.datetime.now().strftime('%H%M%S') + '.csv'
csv = open(filename, 'a+')

# print header
csv.write ('time s, ')
numberOfAnchors = 9
for i in range(0, numberOfAnchors):
    for j in range(i + 1, numberOfAnchors):
        csv.write(str(i + 1) + str(j + 1) + ', ')

csv.write('N, E, D, vN, vE, vD\n')

interrupted = False
skipThisTdoa = True
inline = str()
newTdoa = False

while 1:
    if ser.in_waiting > 0:
        inline = ser.readline()
        newTdoa == False
        if skipThisTdoa == True:
            skipThisTdoa = False
        else:
            csv.write(str(oldTimestamp))
            csv.write(',')
            csv.write(inline.decode('ascii').rstrip())
            inline = str()
            csv.write(',')
            csv.write(','.join(map(str, NatNetCoords)))
            csv.write(',')
            csv.write(','.join(map(str, NatNetVel)))
            csv.write('\n')
            csv.flush()
            print(NatNetCoords, NatNetVel)
            

    if interrupted:
        print ("Closing...")
        break

csv.close()
# thread.join()
        

