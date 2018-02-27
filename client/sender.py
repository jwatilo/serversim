#!/usr/bin/env python3

from argparse           import ArgumentParser
from socket             import AF_INET
from socket             import SOCK_STREAM
from socket             import gethostname
from socket             import socket 
from sys                import exit

MAX_REPLY_SIZE = 2048

def parse_options():
    parser = ArgumentParser( description='TCP Client' )
    parser.add_argument( '-host'
                       , action='store'
                       , dest='host'
                       , required=False
                       , help='the host to connect to (default: localhost)'
                       , type=str
                       , default=gethostname()
                       )
    parser.add_argument( '-port'
                       , action='store'
                       , dest='port'
                       , required=True
                       , help='the port to connect to'
                       , type=int
                       )
    parser.add_argument( '-msg'
                       , action='store'
                       , dest='msg'
                       , required=True
                       , help='the message to send'
                       , type=str
                       )
    return vars( parser.parse_args() )

if __name__ == '__main__':
    options = parse_options()

    # create a socket object
    sock = socket( AF_INET, SOCK_STREAM )

    # get local machine name
    host = options['host']

    # get port
    port = options['port']

    # get message
    msg = options['msg']

    # connection to hostname on the port.
    sock.connect( (host, port) )
    print( 'Connected to server' )

    # send message
    sock.sendall( '{}\n'.format( msg ).encode() )
    print( 'Sent message: {}'.format( msg ) )

    reply = sock.recv( MAX_REPLY_SIZE )

    sock.close()

    print( 'Received response: {}'.format( reply.decode() ) )

    exit( 0 )

