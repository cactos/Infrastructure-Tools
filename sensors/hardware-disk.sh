#!/bin/bash

echo -ne "disk_name\t"
echo -ne "disk_parent\t"
echo -ne "disk_type\t"
echo -ne "disk_size\t"
echo -ne "disk_device\t"
echo -ne "disk_mount\n"

# collect partitions, sort by name and concatenate parent items
declare -A LIST_FIELDS
declare -A LIST_PARENTS
while IFS= read -r -d $'\n' line; do
	IFS=';' read -a arr <<< "$line"
	NAME=${arr[0]}

	# detect if HDD,SDD or -
	isHdd=-1
	if [ -e /sys/block/${arr[0]}/queue/rotational ]; then
		isHdd=$(cat /sys/block/${arr[0]}/queue/rotational)
	fi
	if [[ $isHdd == "1" ]]; then
		isHdd="HDD"
	else if [[ $isHdd == "0" ]]; then
		isHdd="SSD"
	else
		isHdd="-"
	fi; fi
	
	if [ -z "${arr[1]}" ]; then
     arr[1]="-"
    fi;
    
    if [ -z "${arr[4]}" ]; then
     arr[4]="-"
    fi;
	
	# Store fields type, size, isHdd, mountpoint
	LIST_FIELDS[$NAME]="${arr[2]}\t${arr[3]}\t$isHdd\t${arr[4]}"

	# Lookup if device appeared already, if so, attend parent device
	if [ ${LIST_PARENTS[$NAME]+exists} ]; then
		if [ "${LIST_PARENTS[$NAME]}" != "${arr[1]}" ]; then
			LIST_PARENTS[$NAME]=${LIST_PARENTS[$NAME]}${LIST_PARENTS[$NAME]+,}${arr[1]}
		fi	
	else
		LIST_PARENTS[$NAME]=${arr[1]}
	fi

done < <(lsblk -r -o NAME,PKNAME,TYPE,SIZE,MOUNTPOINT |tail -n+2  | tr " " ";")

# print collected results
for name in "${!LIST_FIELDS[@]}"
do
	echo -ne $name"\t"
	echo -ne ${LIST_PARENTS[$name]}"\t"
	echo -ne ${LIST_FIELDS[$name]}"\n"
done