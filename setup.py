from setuptools import find_packages
from setuptools import setup

setup( name             = 'serversim'
     , version          = '1.0.0'
     , author           = 'John Watilo'
     , author_email     = 'john@johnwatilo.com'
     , description      = 'A sample Python TCP server application that doesn\'t do much.'
     , keywords         = 'serversim'
     , packages         = find_packages() 
     , url              = 'http://github.com/jwatilo/serversim'
     , long_description = read( 'README.md' )
     , install_requires = ['coverage']
     )
