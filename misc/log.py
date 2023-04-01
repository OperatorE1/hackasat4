import sys
import os
import os.path
import re
import time
import logging
import random

logging.TRACE = 25
logging.addLevelName(logging.TRACE,'TRACE')

logging.DEBUG2 = 7
logging.addLevelName(logging.DEBUG2,'DEBUG2')
logging.DEBUG3 = 6
logging.addLevelName(logging.DEBUG3,'DEBUG3')


log_level = logging.WARNING
write_console = True

class UsageException(Exception):
    pass

def setConsoleOut(write=True):
    global write_console
    write_console = write

def setLvl(verbose):
    global log_level
    if verbose == 1:
        log_level = logging.TRACE
    elif verbose == 2:
        log_level = logging.INFO
    elif verbose == 3:
        log_level = logging.DEBUG
    elif verbose == 4:
        log_level = logging.DEBUG2
    elif verbose == 4:
        log_level = logging.DEBUG3
    else:
        log_level = logging.ERROR

stdout_lvl = 4
stderr_lvl = 3


def setupLogging(log_dir=os.getcwd(), stdout_wrapper=None,stderr_wrapper=None,log_file='run.log',lvl=None, logger=''):

    formatting = "(%(asctime)s %(filename)s:%(lineno)-4s %(levelname)-8s" + "%s"%(logger) + "): %(message)s"
    datefmt = '%a, %d %b %Y %H:%M:%S'
    fmtr = logging.Formatter(formatting,datefmt)

    root_logger = logging.getLogger('')

    for h in root_logger.handlers:
        root_logger.removeHandler(h)

    root_logger.setLevel(1)

    ## setup default trace output
    setattr(logging, 'trace', lambda *args: root_logger.log(logging.TRACE, *args))
    setattr(logging, 'debug2', lambda *args: root_logger.log(logging.DEBUG2, *args))
    setattr(logging, 'debug3', lambda *args: root_logger.log(logging.DEBUG3, *args))

    ## setup console log output
    sth = logging.StreamHandler(sys.__stdout__) # make everything go to stdout
    if lvl:
        setLvl(lvl)
    sth.setLevel(log_level)
    sth.setFormatter(fmtr)
    root_logger.addHandler(sth)

    ## setup log file output
    log_file = os.path.join(log_dir,log_file)
    if os.path.exists(log_file):
        # don't delete old file, create a new one
        #logging.warn('log file [%s] already exists, overwriting' %(log_file) )
        #os.remove(log_file)

        p,e = os.path.splitext(log_file)
        rand = random.random()
        log_file = p + '-%s-%f'%(time.strftime("%Y%m%d_%H%M%S"),rand) + e
        logging.warn('using log %s instead'%log_file)
        
        # TODO-2: FIXME: this isn't the correct way to remove the old hander
        #if root_logger.handlers[0]:
        #    root_logger.handlers[0].stream.close()
        #    root_logger.removeHandler(root_logger.handlers[0])

    fhnd = logging.FileHandler(log_file)
    fhnd.setLevel(1)
    fhnd.setFormatter(fmtr)
    root_logger.addHandler(fhnd)

    ## capture all stdout, stderr as well to redirect to log file
    if stdout_wrapper:
        sys.stdout = stdout_wrapper    
    if stderr_wrapper:
        sys.stderr = stderr_wrapper

    def debug_factory(logger, debug_level):
        def custom_debug(msg, *args, **kwargs):
            if logger.level >= debug_level:
               return
            logger._log(debug_level, msg, args, kwargs)
        return custom_debug        

    if stdout_wrapper or stderr_wrapper:
        # child logger for console messages
        logging.setLoggerClass(MyLogger)
        msg_logger = logging.getLogger('MSG')
        msg_logger.setLevel(1)  # write everything out
        msg_logger.propagate = False        # don't let the root handler process this

        logging.addLevelName(stdout_lvl, 'STDOUT')
        logging.addLevelName(stderr_lvl, 'STDERR')
        #setattr(msg_logger, 'stdout', debug_factory(msg_logger, logging.STDOUT))
        #setattr(msg_logger, 'stderr', debug_factory(msg_logger, logging.STDERR))

        if msg_logger.handlers:
            msg_logger.handlers[0].stream.close()
            msg_logger.removeHandler(msg_logger.handlers[0])
    
        fhnd = logging.FileHandler(log_file)
        fhnd.setLevel(1)
        fhnd.setFormatter(fmtr)
        msg_logger.addHandler(fhnd)

class MyLogger(logging.getLoggerClass()):
    def makeRecord(self, *args):
        name, level, fn, lno, msg, args, exc_info, func, extra = args
        if extra is not None:
        #    for key in extra:
        #        setattr(dir(), key, extra[key])
            fn = extra['fn']
            lno = extra['lno']
            func = extra['func']
        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        return rv

if __file__[-4:].lower() in ['.pyc', '.pyo']:
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

import io
class OutWrapper(io.IOBase):
    def findCaller(self):
        f = sys._getframe()
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        return rv
        
    def writelog(self, msg):
        msg = msg.rstrip('\n').lstrip('\n')
        if msg:
            logger = logging.getLogger('MSG')
            fn, lno, func = self.findCaller()
            logger = logging.LoggerAdapter(logger,{'fn':fn, 
                                                   'lno':lno,
                                                   'func':func,
                                                    } )
            logger.log(self.lvl,msg)

class StdOutWrapper(OutWrapper):
    def __init__(self):
        self.lvl = stdout_lvl
    def write(self,msg):
        if write_console:
            sys.__stdout__.write(msg)
            sys.__stdout__.flush()
        self.writelog(msg)

class StdErrWrapper(OutWrapper):
    def __init__(self):
        self.lvl = stderr_lvl
    def write(self,msg):
        if write_console:
            sys.__stderr__.write(msg)
            sys.__stderr__.flush()
        self.writelog(msg)


################################################################################
#
# TODO-1: automatically get function name and params for trace output,
# allow for other content to be passed in
#
# TODO-1: use correct stack location (filename:ln) for trace,
# debug[23] output
