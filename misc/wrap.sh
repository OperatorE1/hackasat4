#!/bin/bash

TERM=$(test -t 1)

USAGE="\
Usage: $0 [-h] [-t second] cmd...
  cmd  	       : command to execute
  -h	       : help
  -d	       : debug
  -t seconds   : echo trace line every seconds
"

TRACE=
DEBUG=
while getopts "hdt:" opt; do
    case ${opt} in
	[d]) DEBUG=True ;;
	[t]) TRACE=$OPTARG ;; 
	[h?])
	    echo "$USAGE" 1>&2;
	    exit 1;
	    ;;
    esac
done
shift $((OPTIND-1))

if [ $# -lt 1 ]; then
    echo "$USAGE" 1>&2
    exit 1
fi

curDate=$(date +"%F_%H%M%S")
LOGFILE=$(basename $1)-${curDate}.log
ln -sf "$LOGFILE" "$(basename $1)-latest.log"


################################################################################
function start_watch() {
    set -m
    ( 
	while true; do
	    # look for tee in parents proc group and
	    tpid=$(pgrep -g $$ -f tee.*fifo)
	    #echo "("$(date +"%F_%T.%N")") watch" "["$(ps -q ${app_pid} -o cmd=)"]" $tpid ${*} >&2
	    if ! ps -q $app_pid >/dev/null; then      # 0 exists: 1 doesn't exist
		kill $tpid
	    fi
	    sleep 1
	done
    ) &
    set +m
    watch_pid=$!
}

function end_watch() {
    if [ -z "$watch_pid" ]; then 
	return
    fi
    if [ "$DEBUG" ]; then
	echo "("$(date +"%F_%T.%N")") end_watch" ${*} >&1
    fi
    pkill -9 -g $watch_pid
}    

function start_trace() {
    set -m    
    ( 
	while true; do
	    echo "("$(date +"%F_%T.%N")") trace"  ${*} >&2
	    sleep $TRACE
	done
    ) &
    set +m
    trace_pid=$!
}

function end_trace() {
    if [ -z "$trace_pid" ]; then 
	return
    fi
    if [ "$DEBUG" ]; then
	echo "("$(date +"%F_%T.%N")") end_trace" ${*} >&1
    fi
    pkill -9 -g $trace_pid
}

function start_tee() {
    exec  6<&0
    exec  7>&1
    exec  8>&2
    
    fifo=$tmpdir/fifo-tee
    mkfifo $fifo

    set -m
    ( tee <$fifo ${LOGFILE} ) & 
    set +m
    tee_pid=$!
    exec 1>&-
    exec 1>$fifo
    exec 2>&-
    exec 2>$fifo
}

function end_tee() {
    if [ -z "$tee_pid" ]; then 
	return
    fi
    if [ "$DEBUG" ]; then
	echo "("$(date +"%F_%T.%N")") end_tee" ${*} >&1
    fi
    
    pkill -9 -g $tee_pid

    exec 0<&6-
    exec 1>&7-
    exec 2>&8-
}

function end() {
    if [ "$DEBUG" ]; then
	echo "("$(date +"%F_%T.%N")") end" ${*} >&1
    fi
    #ls -l /proc/$$/fd

    end_watch
    end_trace
    end_tee
    
    #ls -l /proc/$$/fd
    rm -rf $tmpdir
    #echo "end"
}


function start() {
    #echo "start"
    tmpdir=$(mktemp -d) || exit 1
  
    start_tee
    if [ "$TRACE" ]; then
	start_trace
    fi
    
    trap "\
    end early1 ${*};
    exit 5" INT TERM KILL
    if [ "$DEBUG" ]; then
	echo "("$(date +"%F_%T.%N")") start..." >&1
    fi
}

################################################################################
#ls -l /proc/$$/fd
start

fifoa=$tmpdir/fifo-app
mkfifo $fifoa

#stty tostop

####################
set -m
( ${*} <$fifoa ) &
app_pid=$!
set +m
####################
start_watch

trap "\
pkill -TERM -g $app_pid;
end early2 ${*};
exit 5" INT TERM KILL

(tee $fifoa) 2>/dev/null        # forground to capture all tty input and pass along to stdin pipe to app

wait $app_pid     # make sure app cleaned up, and get return value
st=$?

end nicely: ${*};
trap - INT TERM KILL

#ls -l /proc/$$/fd
exit $st


TODO-2: suppress Terminated messge from tee forground capture proc when killed by watcher
