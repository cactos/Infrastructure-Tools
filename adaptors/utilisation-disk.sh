#!/bin/bash

# depends on iostat
# install: yum install sysstat
x=1 # 1 second
while IFS= read -r -d $'\n' line; do
	device=$(echo $line | cut -d ' ' -f1)
	
	## check and print headline
	if [[ "$device" == "Device:" ]]; then
		
		echo -ne $line"\tMountpoint\n"
		continue
	fi
	
  ## lookup mountpoint
    mountpoint=""
    if [[ ! -z $device ]]; then
            mountpoint=$(mount -l | grep "$device " | cut -d ' ' -f3)
            if [ -z "$mountpoint" ]; then
                    mountpoint="-"
            fi;
    fi

    ## print measurement line
    if [[ ! -z "$mountpoint" ]]; then
            echo -ne $line"\t"$mountpoint"\n"
    fi;
done < <(iostat -p ALL -d -N -y $x 1 | tail -n+3)
# blocking for $x seconds