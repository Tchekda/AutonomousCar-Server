import socket
import sys
from threading import Thread, Timer
import time
from pythonSB import servo_get, servo_set, servo_configure, servo_set_angle, servo_map
import traceback
import pixy
from ctypes import Structure, c_uint
import pixy

class Blocks (Structure):
  _fields_ = [ ("m_signature", c_uint),
    ("m_x", c_uint),
    ("m_y", c_uint),
    ("m_width", c_uint),
    ("m_height", c_uint),
    ("m_angle", c_uint),
    ("m_index", c_uint),
    ("m_age", c_uint) ]

received_data = {
    "speed": 0,
    "keep": 0,
    "angle": 0
}

    
def keepSpeed():
    while True:
        if (received_data['speed'] != None) :
            if (received_data['keep'] and received_data['speed'] != 0):
                servo_set(0, speedToFreq(received_data['speed']))
            time.sleep(0.1)
        else :
            print("Stoping thread")
            break

def speedToFreq(speed):
    freq = 150
    if(speed > 0):
        freq = servo_map(speed, 0, 50, 149, 116)
    elif (speed < 0):
        freq = servo_map(speed, -20, 0, 250, 158)
    return freq

def sendData(connection):
    data = ""
    data += "speed=" + str(received_data['speed']) + "|"
    data += "keep=" + str(int((received_data['keep']))) + "|"
    data += "angle=" + str(received_data['angle']) + "|"
    data = ((data + "\n").encode("UTF-8"))
    connection.sendall(data)

def updateSpeed(oldSpeed, connection):
    global received_data
    if (oldSpeed == received_data['speed'] and oldSpeed != -20 and oldSpeed != 50 and oldSpeed != 0 and received_data['keep'] == False): #Speed hasn't evolved
        received_data['speed'] = 0
        print("Speed has been reset")
        #servo_set(0, 150)
        sendData(connection)


def main():
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the port
    server_address = ('0.0.0.0', 2020)
    print('starting up on %s port %s' % server_address)
    sock.bind(server_address)
    # Listen for incoming connections
    sock.listen(1)

    while True:
        global received_data
        # Wait for a connection
        print('waiting for a connection')
        received_data['keep'] = 0
        received_data['speed'] = 0
        received_data['angle'] = 0
        servo_set_angle(1, received_data['angle'])
        try:
            connection, client_address = sock.accept()
        except KeyboardInterrupt:
            print("Keyboard Stop")
            break
        try:
            print('connection from', client_address)
            sendData(connection)
            # Receive the data in small chunks and retransmit it
            while True:
                try:
                    data = connection.recv(2048)
                    if data:
                        #print('received "%s"' % data)
                        pairs = data.rstrip().decode("UTF-8").split("|")
                        received = {}
                        for pair in pairs :
                            try: 
                                text = pair.split("=")
                                if (len(text) == 2 and text[0] != ""):
                                    text[0] = text[0].replace('\n', '')
                                    received[text[0]] = text[1]
                            except:
                                pass
                        if(len(received) > 0):
                            print('formatted "%s"' % received)
                            for key, value in received.items():
                                if key == 'speed':
                                    try : 
                                        received_data['speed'] = int(value)
                                        if(int(received['keep']) == 1):
                                            received_data['keep'] = bool(int(received['keep']))
                                        else:
                                            servo_set(0, speedToFreq(received_data['speed']))
                                            t = Timer(1.5, updateSpeed, args=[received_data['speed'], connection])
                                            t.start()
                                    except OSError:
                                        pass
                                elif key == "keep":
                                    try:
                                        if(int(value) == 0):
                                            received_data['keep'] = 0
                                    except OSError:
                                        pass
                                elif key == "angle":
                                    try:
                                        angle = int(value)
                                        if(angle >= -90 and angle <= 90):
                                            received_data['angle'] = angle
                                            #servo_set_angle(1, angle)
                                    except OSError:
                                        pass
                            sendData(connection)

                        else:
                            print('received "%s"' % data)
                            print('formatted "%s"' % received)
                    else :
                        connection.close()
                        break
                except KeyboardInterrupt:
                    connection.close()
                    break
        except socket.error:
            traceback.print_exc()
        except:
            connection.close()
            traceback.print_exc()
            break
    sock.close()
    print("Socket Closed")

if __name__ == '__main__':
    print("Starting the server..")
    thread = Thread(target=keepSpeed)
    print("Thread initialized")
    thread.start()
    print("Thread started")
    servo_configure(1, 85, 215, -90 , 90)
    print("Servo initialized")   
    # pixy.init ()
    # pixy.change_prog ("color_connected_components")
    # pixy.set_lamp (0, 0)
    # print("Pixy initialized")
    # height = pixy.get_frame_height()
    # width = pixy.get_frame_width()
    # print("Resolution : ", width, "by", height)
    main()
    print("Main loop finished")
    received_data['speed'] = None
    thread.join()
    print("Thread joined")
