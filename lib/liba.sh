#!bash #shebang for editor/syntax highlighting only, include with source builtin, dont run on its own
# shellcheck disable=SC2034
#
# Copyright (c) 2017 Regents of The University of Michigan.
# All Rights Reserved.
#

##############################################################################
#
#                     ### a library for bash scripts ###
#
# How to use:
#
# At the top of you script, define variables USAGE, HELP, ARG_HELP,
# CHECK_PROGS, SHORT_OPTIONS, and LONG_OPTION and the function handle_options,
# as needed, and then source this library, followed by the main part of your
# script.  For example:
#
#    #!/bin/bash
#    USAGE="[--help|-h|--some-arg|-a] [--other-arg <foo>]"
#    HELP="myprog is a script to do such and such"
#    ARG_HELP="    --some-arg -a   Enable something
#         --other-arg <foo>   Use a foo for bla bla
#    "
#    CHECK_PROGS="gunzip idba_ud fastqc"
#    SHORT_OPTIONS=so:
#    LONG_OPTION=--some-arg,--other-arg:
#    handle_options () {
#        if [ "$#" -gt 0 ]; then
#    	case "$1" in
#    	    (--some-arg|-s)
#    	        SOME_ARG=true
#    	        return 1;;
#    	    (--other-arg|-o)
#    	        OTHER_ARG="${2}"
#    	        return 2;;
#            esac
#        else
#            return 0
#        fi
#    }
#   
#    . "$(dirname "$0")/../lib/liba.sh" || echo "Failed to source script library"
#
#    # your script comes here --->
#
# The return code of handle_options is the number of consumed arguments,
# so usually 1 or 2. Positional parameters are still stored in $@.
#
# The following variables are provided:
#
#   WORK_DIR
#   VERBOSE_FLAG
#   V
#
# The following functions are provided:
#
#   abort
#   debug
#   error
#   info
#   warning
#
##############################################################################
set -e
trap 'exception $LINENO $?' ERR

usage() {
    if [ "$VERBOSITY" -ge 1 ]; then
	echo "
USAGE: $SCRIPT_NAME $USAGE
"
    fi
}

user_help() {
    echo "$SCRIPT_NAME - $HELP"
    usage
    echo "Command line parameters:
    --working-dir <path>  Where to retrieve and store files
-h  --help          Print this help.
    --no-color      Disable colorful output.
-v                  Verbosity: use multiple -v to increase output.
    --verbosity <n> Set level verbosity.
    $ARG_HELP
"
}

exception () {
    echo "[${RED}ERROR${ENDCOLOR}] at line $1; error code $2"
}

debug() {
    [ "$VERBOSITY" -lt 3 ] || echo "[$SCRIPT_NAME] [DEBUG] $1"
}

info() {
    [ "$VERBOSITY" -lt 1 ] || echo "[$SCRIPT_NAME] $1"
}

warning() {
    [ "$VERBOSITY" -lt 1 ] || echo -e "[$SCRIPT_NAME] [${ORANGE}WARNING${ENDCOLOR}] $1"
}

error() {
    [ "$VERBOSITY" -lt -1 ] || >&2 echo -e "[$SCRIPT_NAME] [${RED}ERROR${ENDCOLOR}] $1"
}

abort() {
    # write an error message and exit.  If the last positional parameter is 'usage' then also print the usage text.
    >&2 echo -e "[$SCRIPT_NAME] [${RED}ABORT${ENDCOLOR}] $1"
    if [ "$VERBOSITY" -ge 0 ]; then
	if [ $# -ge 0 ]; then
	    [ "${!#}" == "usage" ] && usage
	fi
    fi
    exit 1
}

# get name of this script
SCRIPT_NAME=$(basename "$0")

##########################
# default variable values
##########################
#
WORK_DIR=$(pwd)
# default verbosity level
VERBOSITY=1
# Enable colorful output by default
USE_COLOR=true

###################################3
# command line parameter handling
###################################
GETOPT_SHORT=hv${SHORT_OPTIONS}
GETOPT_LONG=${LONG_OPTIONS},help,no-color,working-dir:,verbosity:
if which getopt >/dev/null 2>&1; then
    getopt -T || getopt_test="$?"
    if [ "$getopt_test" == 4 ]; then
        # GNU getopt available 
        _getopt=$(getopt -o "$GETOPT_SHORT" --long "$GETOPT_LONG" --name "$SCRIPT_NAME" -- "$@")
        if [ "$?" != 0 ]; then usage; exit 1; fi
    else
	# for non-GNU getopt (on MacOSX?)
	# try best effort without handling long options
	# TODO: this path needs testing
        _getopt=$(getopt -o "$GETOPT_SHORT" --name "$SCRIPT_NAME" -- "$@")
        if [ "$?" != 0 ]; then usage; exit 1; fi
    fi
    # reset $n parameters
    eval set -- "$_getopt"
fi

# handle options arguments / should work with/without getopt
while [ "$#" -gt 0 ]; do
    if type handle_options >/dev/null 2>&1; then
        handle_options "$@" && shifts=0 || shifts="$?"
	if [ "$shifts" -gt 0 ]; then
            for ((i=0; i<shifts; i++)); do shift; done
            continue
	fi
    fi
    case "$1" in
	(--working-dir)
	    WORK_DIR="$2"
            shift
	    ;;
	(-h|--help) user_help; exit 0;;
	(--no-color) USE_COLOR=false;;
	(-v) VERBOSITY=$((VERBOSITY+1));;
	(--verbosity)
	    VERBOSITY="$2"
	    [[ "$VERBOSITY" =~ ^[[:digit:]]+$ ]] || abort "Verbosity level must be a positive integer." usage 
	    shift
	    ;;
	(--) shift; break;;
	(-|-*) abort "invalid command line option: $1" usage;;
	(*) break;; # getopt failure? assume this and following are non-option args
    esac
    shift
done

##########################################################
# color output
#
# for color codes see:
# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
if [ "$USE_COLOR" == true ]; then
    if which tput >/dev/null 2>&1 && [ "$(tput colors)" -ge 8 ]; then
	RED=$(tput setaf 1)
	ORANGE=$(tput bold)$(tput setaf 1)
	ENDCOLOR=$(tput sgr0)
    fi
fi

debug "command line options: $_getopt"
debug "verbosity set to: $VERBOSITY"
# set bash script debugging
[ "$VERBOSITY" -ge 4 ] && set -x
# forward verbosity to other commands
[ "$VERBOSITY" -ge 2 ] && VERBOSE_FLAG=-v
V=$VERBOSE_FLAG

####################################
# check presence of necessary tools
####################################
for i in $CHECK_PROGS; do
    which "$i" > /dev/null 2>&1 || abort "$i command is not available."
done
