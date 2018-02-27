#!/usr/bin/env python3

from os         import path
from setuptools import setup

def read( fname ):
    return open( path.join( path.dirname( __file__ ), fname ) ).read()

setup( name             = 'serversim'
     , version          = '1.0.0'
     , author           = 'John Watilo'
     , author_email     = 'john@johnwatilo.com'
     , description      = 'A sample Python TCP server application that doesn\'t do much.'
     , keywords         = 'serversim'
     , packages         = ['service', 'client', 'tests']
     , url              = 'http://github.com/jwatilo/serversim'
     , long_description = read( 'README.md' )
     )
