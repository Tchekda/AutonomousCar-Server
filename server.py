import socket
import sys
from threading import Thread
import time
from pythonSB import *
import traceback


speed = 0

def keepSpeed():
    while True:
        if (speed >= 0) :
            if (speed > 115 and speed < 149):
                servo_set(0, speed)
            time.sleep(0.1)
        else :
            break

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
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = sock.accept()
        try:
            print('connection from', client_address)

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
                        connection.sendall(data)
                        if(len(received) > 0):
                            #print('formatted "%s"' % received)
                            for key, value in received.items():
                                global speed
                                if key == 'speed':
                                    try : 
                                        if(received['keep'] and int(received['keep']) == 1):
                                            speed = int(value)
                                        else:
                                            servo_set(0, int(value))
                                    except OSError:
                                        pass
                                elif key == "keep":
                                    speed = 0
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
            print('client interrompu')
            traceback.print_exc()
        except:
            connection.close()
            traceback.print_exc()
            break
    sock.close()
    print("Closing")



if __name__ == '__main__':
    thread = Thread(target=keepSpeed)
    thread.start()
    main()
    speed = -1
    thread.join()
