#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
from datetime           import datetime
from os                 import environ
from os                 import getpid
from select             import EPOLLIN
from select             import EPOLLHUP
from select             import EPOLLERR
from select             import epoll
from socket             import AF_INET
from socket             import IPPROTO_TCP
from socket             import SO_REUSEADDR
from socket             import SO_KEEPALIVE
from socket             import SO_LINGER
from socket             import SOCK_STREAM
from socket             import SOL_SOCKET
from socket             import SHUT_WR
from socket             import SHUT_RD
from socket             import TCP_NODELAY
from socket             import gethostname
from socket             import socket
from struct             import pack
from sys                import exit
from time               import sleep

TCP_BACKLOG   = 1024
MAX_THREADS   = 128
SHUT_ME_DOWN  = False
CONTAINERIZED = False
LVL_INFO      = 'INFO    '
LVL_WARNING   = 'WARNING '
LVL_ERROR     = 'ERROR   '
LVL_CRITICAL  = 'CRITICAL'
EXIT_CODE     = 0
CONTAINER_ID  = None

def say( msg, level=LVL_INFO ):
    if CONTAINERIZED:
        message = '{1:} listener.py: {2:}'.format( level, msg )
    else:
        message = '{0:%Y-%m-%d %H:%M:%S} {1:} listener.py[{2:}]: {3:}'.format( datetime.now(), level, getpid(), msg )
    print( message )

def respond( num, clientsocket, text ):
    say( 'Thread {} - RESPONSE: {}'.format( num, text.replace( '\n', '\\n' ) ) )
    clientsocket.sendall( text.encode() )

def handle_connection( num, clientsocket, addr ):
    clientsocket.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
    clientsocket.setsockopt( SOL_SOCKET, SO_KEEPALIVE, 1 )

    # read incoming request
    data = None
    while data is None:
        data = clientsocket.recv( 2048 )

    # evalute and reply
    if data is not None:
        say( 'Thread {} - Got request from {}'.format( num, str( addr ) ) )

        data = data.decode().strip()
        say( 'Thread {} - REQUEST: {}'.format( num, data ) )

        if '<ucm>' in data:
            clientsocket.sendall( pack( '!i', 16 ) )
            clientsocket.sendall( pack( '!i', 2 ) )
            clientsocket.sendall( str.encode( 'REST00010001OK' ) )
            say( 'Thread {} - ASV2 message received, reply sent'.format( num ) )
            sleep( 100 / 1000 ) # sleep for 100 ms go give client time to read reply

        else:
            tokens = data.split()
            command = tokens[0].upper()

            if command == 'ECHO':
                respond( num, clientsocket, ' '.join( tokens[1:] ) )

            elif command == 'ERROR':
                say( ' '.join( tokens[1:] ), level=LVL_ERROR )
                respond( num, clientsocket, 'OK' )

            elif command == 'PING':
                respond( num, clientsocket, 'OK' )

            elif command == 'SHUTDOWN':
                say( 'Thread {} - Shutting down per client request...'.format( num ) )
                global SHUT_ME_DOWN
                SHUT_ME_DOWN = True
                respond( num, clientsocket, 'OK' )

            elif command == 'WAIT':
                if len( tokens ) > 1:
                    try:
                        ms = int( tokens[1] )
                        say( 'Thread {} - Waiting for {} milliseconds...'.format( num, ms ) )
                        sleep( ms / 1000 )
                        respond( num, clientsocket, 'OK' )
                    except ValueError:
                        respond( num, clientsocket, 'ERR_INVALID_WAIT_TIME' )
                else:
                    respond( num, clientsocket, 'ERR_MISSING_WAIT_TIME' )

            elif command == 'HELP':
                respond( num, clientsocket, '=-=-=-=-=-=-=-=-=-=-=\n'
                                          + ' Available Commands\n'
                                          + '=-=-=-=-=-=-=-=-=-=-=\n'
                                          + '<ucm>.*</ucm> ... Respond to ASv2 message\n'
                                          + 'HELP ............ Show help\n'
                                          + 'ECHO <str> ...... Where <str> is a string to echo back\n'
                                          + 'ERROR <str> ..... Print <str> as an ERROR message\n'
                                          + 'PING ............ Test connection\n'
                                          + 'SHUTDOWN ........ Stop the server\n'
                                          + 'WAIT <ms> ....... Wait for <ms> millseconds then return\n'
                                          )

            else:
                respond( num, clientsocket, 'ERR_INVALID_REQUEST' )

    clientsocket.shutdown( SHUT_WR )
    clientsocket.close()

def leave():
    if EXIT_CODE == 0:
        say( 'Exit Code: {}'.format( EXIT_CODE ) )
    else:
        say( 'Exit Code: {}'.format( EXIT_CODE ), level=LVL_CRITICAL )
    exit( EXIT_CODE )

def set_containerized():
    # check to see if I'm running in a container
    global CONTAINER_ID
    global CONTAINERIZED
    CONTAINER_ID = gethostname()
    docker_string = '/docker-{}'.format( CONTAINER_ID[:12] )
    try:
        with open( '/proc/1/cgroup', 'r' ) as f:
            for line in f:
                if docker_string in line:
                    CONTAINERIZED = True
                    CONTAINER_ID = CONTAINER_ID[:12]
                    break
    except Exception as e:
        say( 'Unable to open file [{}]: {}'.format( '/proc/1/cgroup', str( e ) ), level=LVL_WARNING )

def start_listener():
    global SHUT_ME_DOWN
    set_containerized()

    # get port
    port = environ.get( 'TCP_SERVER_PORT' )
    if port is None:
        say( 'Environment variable TCP_SERVER_PORT was not set', level=LVL_CRITICAL )
        EXIT_CODE = 1
        leave()
    try:
        port = int( port )
    except ValueError as e:
        say( 'Environment variable TCP_SERVER_PORT is not numeric [{}]'.format( port ), level=LVL_CRITICAL )
        EXIT_CODE = 3
        leave()

    say( '*** =-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=' )
    say( '***  Welcome to SeRvErSiM DOCKER Edition!'  )
    say( '*** =-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=' )
    if CONTAINERIZED:
        say( '***  CONTAINER_ID ...... {}'.format( CONTAINER_ID ) )
    else:
        say( '***  HOST .............. {}'.format( CONTAINER_ID ) )
    say( '***  TCP_SERVER_PORT ... {}'.format( port         ) )
    say( '***  MAX_THREADS ....... {}'.format( MAX_THREADS  ) )
    say( '***  TCP_BACKLOG ....... {}'.format( TCP_BACKLOG  ) )
    say( '*** =-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=' )
    if CONTAINERIZED:
        say( 'Running INSIDE of a container' )
    else:
        say( 'Running OUTSIDE of a container' )

    # create client thread pool
    say( 'Creating client thread pool' )
    pool = ThreadPoolExecutor( max_workers=MAX_THREADS )

    # create map to keep track of futures (threads in the pool)
    future_map = {}

    # create a socket object
    say( 'Creating listener socket' )
    serversocket = socket( AF_INET, SOCK_STREAM )

    # bind to the port
    say( 'Binding to port {}'.format( port ) )
    serversocket.bind( ('0.0.0.0', port) )

    # backlog up to TCP_BACKLOG requests
    serversocket.listen( TCP_BACKLOG  )

    # set socket options 
    serversocket.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
    serversocket.setsockopt( SOL_SOCKET, SO_KEEPALIVE, 1 )
    serversocket.setsockopt( SOL_SOCKET, SO_LINGER, pack( 'ii', 1, 0 ) )

    # make it a non-blocking socket and use polling model
    serversocket.setblocking( 0 )
    epoll_mask    = EPOLLIN | EPOLLHUP | EPOLLERR
    polling_model = epoll()
    polling_model.register( serversocket.fileno(), epoll_mask )
    sockets    = {}
    addresses  = {}
    request_number = 0

    say( 'Ready for requests!' )

    while not SHUT_ME_DOWN:

        try:
            # poll for events
            events = polling_model.poll( 0.2 )

            # evaluate the socket events
            for event_fd, event in events:

                if (event & EPOLLERR) or (event & EPOLLHUP):
                    say( 'Client connection lost' )
                    if event_fd == serversocket.fileno():
                        SHUT_ME_DOWN = True
                    else:
                        polling_model.unregister( event_fd )
                        sockets[event_fd].close()
                        del sockets[event_fd]

                elif event & EPOLLIN:
                    try:
                        if event_fd == serversocket.fileno():
                            clientsock, address = serversocket.accept()
                            sockets[clientsock.fileno()] = clientsock
                            addresses[clientsock.fileno()] = address
                            clientsock.setblocking( False )
                            clientsock.setsockopt( IPPROTO_TCP, TCP_NODELAY, 1 )
                            polling_model.register( clientsock.fileno(), epoll_mask )
                        else:
                            # add the client connection to the thread pool
                            request_number += 1
                            future = pool.submit( handle_connection, request_number, sockets[event_fd], addresses[event_fd] )
                            future_map[request_number] = future

                            # prune the map of any that have finished
                            running = 0
                            to_delete = []
                            for k, v in future_map.items():
                                if future_map[k].done():
                                    to_delete.append( k )
                                else:
                                    running += 1
                            for k in to_delete:
                                del future_map[k]

                            # take this opportunity to print pool statistics
                            say( 'POOL STATISTICS:  Max Workers = {}, Num RUNNING = {}, Num WAITING = {}'
                                 .format( MAX_THREADS, running, len( future_map ) - running  )
                               )

                    except Exception as e:
                        say( 'Shutting down due to exception: {}'.format( str( e ) ) )
                        EXIT_CODE = 4
                        SHUT_ME_DOWN = True
                        polling_model.unregister( event_fd )
                        sockets[event_fd].close()
                        del sockets[event_fd]

        except KeyboardInterrupt:
            print( '' ) ;
            say( 'Shutting down due to CTRL+C...' )
            SHUT_ME_DOWN = True

    say( 'Goodbye!' )
    pool.shutdown()
    for sk in sockets.keys():
        sockets[sk].close()
    polling_model.close()
    serversocket.shutdown( SHUT_RD )
    serversocket.close()
    leave()

if __name__ == '__main__':
    start_listener()
