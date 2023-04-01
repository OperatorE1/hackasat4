#!/usr/bin/python

import sys
import logging
import types, operator
import argparse

import log

VERSION='0.1'

def add_options(parser):
    pass

def run(args):
    print("args=%s" % (vars(args)))


#from mygraphc import *


 
module=sys.modules[__name__]
valid_funcs = [getattr(module,a,None).__name__ for a in dir(module)
               if isinstance(getattr(module,a,None), types.FunctionType)]    
valid_funcs = filter(lambda x: x not in ['add_options','main'],valid_funcs)    

def main(*given_args):
    # process arguments
    parser = argparse.ArgumentParser(description='')
    add_options(parser)
    parser.add_argument('--action',nargs=1,default='run',choices=valid_funcs,
                        help='action to perform (default=%(default)s)')
    parser.add_argument('params',nargs=argparse.REMAINDER, help='extra arguments')
    parser.add_argument('-v', '--verbose', action='count',
                        help='Increase verbosity (specify multiple times for more)')
    parser.add_argument('--no_console', action='store_false', default=True,
                        help='disable stdout/err console output')
    args = parser.parse_args( given_args[1:] )

    # setup logging
    log.setupLogging(stdout_wrapper=log.StdOutWrapper(),stderr_wrapper=log.StdErrWrapper(),
                     lvl=args.verbose)
    log.setConsoleOut(args.no_console)

    # execute functions
    try:
        f = operator.methodcaller(args.action,args)
        f(sys.modules[__name__])
    except log.UsageException, ex:
        logging.info('%s'%ex)
        optp.print_help()
    except Exception, ex:
        logging.exception('%s'%ex)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))

