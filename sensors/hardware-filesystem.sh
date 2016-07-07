#!/bin/bash

# requires filebench!
# yum install -y filebech

echo -ne "mount\t"
echo -ne "type\t"
echo -ne "available\t"
echo -ne "used\t"
echo -ne "readbandmax\t"
echo -ne "writebandmax\n"

while IFS= read -r -d $'\n' line; do
	arr=( $(echo $line) )
	
	# execute filesystem benchmark (using dd)
	echo 3 > /proc/sys/vm/drop_caches
	# write bench (oflag=dsync == block until everything is written to disk)
	tmp=$(dd if=/dev/zero of=${arr[0]}testdump bs=1M count=100 oflag=dsync 2>&1) 
	bench_write=$(echo $tmp | cut -d ',' -f3)
	echo 3 > /proc/sys/vm/drop_caches
	# read bench
	tmp=$(dd if=${arr[0]}testdump of=/dev/null bs=1M count=100 2>&1)
	bench_read=$(echo $tmp | cut -d ',' -f3)
	rm -rf ${arr[0]}testdump	
	
	# print fields
	echo -ne ${arr[0]}"\t"
	echo -ne ${arr[1]}"\t"
	echo -ne ${arr[2]}"\t"
	echo -ne ${arr[3]}"\t"
	echo -ne $bench_read"\t"
	echo -ne $bench_write"\t"
	echo -ne "\n"

done < <(df --output=target,fstype,avail,used -x tmpfs -x devtmpfs |tail -n+2)


