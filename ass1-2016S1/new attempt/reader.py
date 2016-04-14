from socket import *

print ("hello")


def createSocket():
    addr = ("localhost", 6000)
    mysock = socket(AF_INET, SOCK_STREAM)
    mysock.setblocking(1)
    mysock.settimeout(5.0)
    mysock.connect(addr)
    return mysock


mysock = createSocket()
mysock.sendall("hello tom")
print (mysock.recv(1024))
mysock.sendall("hello rick")
print (mysock.recv(1024))
mysock.sendall("stop")
