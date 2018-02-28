#!/usr/bin/env python3

from contextlib         import closing
from os                 import environ
from os                 import linesep
from os                 import path
from socket             import AF_INET
from socket             import SOCK_STREAM
from socket             import SOL_SOCKET
from socket             import SO_REUSEADDR
from socket             import SO_LINGER
from socket             import SHUT_RDWR
from socket             import socket
from struct             import pack
from time               import sleep
from threading          import Thread
from unittest           import main 
from unittest           import TestCase

from service            import listener
from client             import sender 

TCP_SERVER_PORT = 9999 

def find_free_port():
    with closing( socket( AF_INET, SOCK_STREAM ) ) as s:
        s.bind( ('localhost',0) )
        return s.getsockname()[1]

def start_service():
    global TCP_SERVER_PORT
    TCP_SERVER_PORT = find_free_port()
    environ[ 'TCP_SERVER_PORT' ] = str( TCP_SERVER_PORT )
    service_thread = Thread( target=listener.start_listener )
    service_thread.start()

    # give the service a moment to get ready
    sleep( 1 )
    return service_thread

def send_message_to_service( message, expected_response ):
    global TCP_SERVER_PORT
    # create a socket object
    sock = socket( AF_INET, SOCK_STREAM )
    response = '' 

    try:
        # connection to hostname on the port.
        sock.connect( ('localhost', TCP_SERVER_PORT) )

        # send message
        sock.sendall( '{}\n'.format( message ).encode() )

        # get response
        bytes_received  = 0
        bytes_expected  = len( expected_response ) 
        bytes_remaining = bytes_expected - bytes_received
        while bytes_remaining > 0:
            data = sock.recv( bytes_remaining )
            bytes_received += len( data )
            bytes_remaining = bytes_expected - bytes_received
            response += data.decode()
    finally:
        sock.close()

    return response
    
def stop_service( service_thread ):
    if service_thread is not None:
        send_message_to_service( 'shutdown', 'OK' ) ;
        service_thread.join()
        service_thread = None

class ServiceTest( TestCase ): 

    @classmethod
    def setUpClass( cls ):
        cls.service_thread = start_service()

    def test_0001_ping( self ):
        expected_response = 'OK'
        actual_response = send_message_to_service( 'ping', expected_response ) ;
        self.assertEqual( expected_response, actual_response ) 

    def test_0002_help( self ):
        expected_response  = '=-=-=-=-=-=-=-=-=-=-=\n'
        expected_response += ' Available Commands\n'
        expected_response += '=-=-=-=-=-=-=-=-=-=-=\n'
        expected_response += '<ucm>.*</ucm> ... Respond to ASv2 message\n'
        expected_response += 'HELP ............ Show help\n'
        expected_response += 'ECHO <str> ...... Where <str> is a string to echo back\n'
        expected_response += 'ERROR <str> ..... Print <str> as an ERROR message\n'
        expected_response += 'PING ............ Test connection\n'
        expected_response += 'SHUTDOWN ........ Stop the server\n'
        expected_response += 'WAIT <ms> ....... Wait for <ms> millseconds then return\n'
        actual_response = send_message_to_service( 'help', expected_response ) ;
        self.maxDiff = None
        self.assertEqual( expected_response, actual_response ) 
    
    def test_0003_echo( self ):
        expected_response = 'The quick brown fox jumped over the lazy dog'
        actual_response = send_message_to_service( 'echo {}'.format( expected_response ), expected_response ) ;
        self.assertEqual( expected_response, actual_response ) 

    def test_0004_error( self ):
        expected_response = 'OK'
        actual_response = send_message_to_service( 'error THIS IS A FAKE ERROR MESSAGE' , expected_response ) ;
        self.assertEqual( expected_response, actual_response ) 

    def test_0005_wait( self ):
        expected_response = 'OK'
        actual_response = send_message_to_service( 'wait 1234' , expected_response ) ;
        self.assertEqual( expected_response, actual_response ) 

    def test_0006_ucm( self ):
        expected_response = '\x00\x00' 
        actual_response = send_message_to_service( '<ucm></ucm>' , expected_response ) ;
        self.assertEqual( expected_response, actual_response ) 

    @classmethod
    def tearDownClass( cls ):
        stop_service( cls.service_thread )
        pass

if __name__ == '__main__':
    main()
