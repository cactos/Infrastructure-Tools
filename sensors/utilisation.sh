#!/bin/bash

echo -ne "cpu_usr\t"
echo -ne "cpu_sys\t"
echo -ne "cpu_wio\t"

echo -ne "mem_free\t"
echo -ne "mem_cache\t"
echo -ne "mem_buff\t"
echo -ne "mem_swpd\t"

echo -ne "net_through\n"


# collect the monitoring data for x seconds
x=1
read -a vals_vmstat < <(vmstat $x 2 | tail -n 1) # blocking $x seconds!
read -a vals_ifstat < <(ifstat ethdata --interval=$x | tail -n 2 | head -n 1) # non-blocking

## calculate network bandwidth
rx=${vals_ifstat[5]}
rx=${rx/K/000} # translate k to "thousand"
tx=${vals_ifstat[7]}
tx=${tx/K/000} # translate k to "thousand"
let netw=$rx+$tx

# print output fields
echo -ne ${vals_vmstat[12]}"\t"
echo -ne ${vals_vmstat[13]}"\t"
echo -ne ${vals_vmstat[15]}"\t"

echo -ne ${vals_vmstat[3]}"\t"
echo -ne ${vals_vmstat[5]}"\t"
echo -ne ${vals_vmstat[4]}"\t"
echo -ne ${vals_vmstat[2]}"\t"
echo -ne $netw"\n"
