from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = ord(string[count+1]) * 256 + ord(string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    """
    @param mySocket: Socket.socket -> host socket
    @param ID: int16 -> process ID
    @param timeout: int -> timeout threshold
    @param destAddr: String -> The destination IP address
    This method acts as the receiving end of the ping.
    Returns the time to ping, or "Request timed out"
    """
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        # Waiting for mySocket to be ready for reading
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)

        if whatReady[0] == []: # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # TODO: parse response -> check if right packet
        #FillInStart
        # Checking for losses
        message = recPacket.decode()
        check = checksum(message)
        if sys.platform == 'darwin':
            check = htons(check) & 0xffff
        else:
            check = htons(check)
        print("Received something")
        
        if recPacket:
            response = f"Response received from {destAddr}"
            response += f""
            return (timeReceived - startedSelect) - howLongInSelect
        #FillInEnd
        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    """
    @param mySocket: Socket.socket -> host socket
    @param destAddr: String -> destination of ping
    @param ID: int16 -> Used in the header to identify the packet
    Constructs a packet and sends it to the correct address
    """

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    # Make a dummy header with a 0 checksum
    myChecksum = 0

    # ICMP header structure: Type, Code, checksum, ID, Sequence
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(str(header + data))

    # Get the right checksum, and put in the header
    # * htons converts 16-bit unsigned integer from host to network byte order
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    # * Sending constructed packet to address
    print(f"Sending ping to {destAddr}...")
    mySocket.sendto(packet, (destAddr, 1))


def ping(host, timeout=1):
    """
    @param host: String -> The host name
    @param timeout: int -> The timeout threshold (1 by default) 
    
    """
    dest = gethostbyname(host)

    icmp = getprotobyname("icmp")
    myID = os.getpid() & 0xFFFF # Return the current process id
    # Send ping requests to a server separated by approximately a second
    sentpackets = 0
    recpackets = 0
    while 1:
        mySocket = socket(AF_INET, SOCK_RAW, icmp)
        sendOnePing(mySocket, dest, myID)
        delay = receiveOnePing(mySocket, myID, timeout, dest)
        print(delay)
        mySocket.close()
        time.sleep(1)

    return delay

if __name__ == "__main__":
    ping("ftp.microsoft.com")
    pass