'''
Created on Aug 24, 2012

@author: bach
'''
from shotgun_replica import config
import time
import sys
import traceback
import pprint

TEMPORARY=0
PARANOID=2
DEBUG=4
INFO=8
WARNING=12
ERROR=16
EXCEPTION=20

IDS={PARANOID:  ["PARANOID  ", 0],
     DEBUG:     ["DEBUG     ", 1],
     INFO:      ["INFO      ", 2],
     WARNING:   ["WARNING   ", 3],
     ERROR:     ["ERROR     ", 4],
     EXCEPTION: ["EXCEPTION ", 5]}

def debug( message, messagelevel = DEBUG, nolinebreak = False, prefix = None ):
    if messagelevel >= config.DEBUG_LEVEL:

        toprint = ""

        timestring = time.strftime( "%Y/%m/%d %H:%M:%S", time.localtime() )
        timestring = timestring + ( "%.3f " % ( time.time() % 1 ) )[1:]
        timestring = timestring + ": " + IDS[messagelevel][0]
        if prefix:
            timestring = timestring + " %s: " % prefix

        if type( message ) == type( "" ) or type( message ) == unicode:
            if not nolinebreak:
                toprint = timestring + ( "\n" + timestring ).join( message.split( "\n" ) ) + "\n"
            else:
                toprint = message
        else:
            if not nolinebreak:
                toprint = timestring + ( "\n" + timestring ).join( pprint.pformat( message ).split( "\n" ) ) + "\n"
            else:
                toprint = message

        toprint = "".join( [x for x in toprint if ord( x ) < 128] )

        if isParanoiing():
            stack = traceback.extract_stack()
            toprint += "  File \"%s\", line %d, in %s\n\n" % ( stack[len( stack ) - 2][0],
                                                               stack[len( stack ) - 2][1],
                                                               stack[len( stack ) - 2][2] )

        if messagelevel >= ERROR:
            sys.stderr.write( toprint )
            sys.stderr.flush()
        else:
            sys.stdout.write( toprint )
            sys.stdout.flush()

def error( message, nolinebreak = False, prefix = None ):
    debug(message, messagelevel = ERROR, nolinebreak, prefix)

def warn( message, nolinebreak = False, prefix = None ):
    debug(message, messagelevel = WARNING, nolinebreak, prefix)

def info( message, nolinebreak = False, prefix = None ):
    debug(message, messagelevel = WARNING, nolinebreak, prefix)

def isDebugging():
    return config.DEBUG_LEVEL < INFO

def isParanoiing():
    return config.DEBUG_LEVEL <= PARANOID
