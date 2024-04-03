#!/bin/bash

declare -a argumentList
argumentList=()
declare -a portList
portList=("1181" "1182" "1183" "1184")
# We only want to stream the usb devices. This flag is set if the previous
# non-tabbed line started with "USB"
isUSB=true

# The printf is to ensure at least two trailing newlines.
# This is important to the loop.
# printf "$(v4l2-ctl --list-devices)\n\n" | while IFS="" ; read -r line ; do
printf "$(cat log.txt)\n\n" | while IFS="" ; read -r line ; do
  if [[ "$line" = $'\t'* ]]; then
    if [ $isUSB = true ]; then
      # xargs trims the tab off the front of the line
      argumentList+=($(echo "$line" | xargs))
    fi
  else
    if [ -n "$argumentList" ]; then
      if [ $isUSB = true ]; then
        bash startOne.sh ${portList[0]} "${argumentList[@]}" &
        # this splicing pops off the first element
        portList=("${portList[@]:1}")
      fi
      argumentList=()
    fi

    # I know, there should be a way of setting a variable to the output of a
    # boolean expression, but I don't think there is...
    if [[ "$line" =~ "(usb" ]]; then
      isUSB=true
    else
      isUSB=false
    fi
  fi
done
