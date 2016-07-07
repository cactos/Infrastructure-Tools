#!/bin/bash

# collect hardware information
cpu_architecture=$(lscpu | grep "Architecture:" | tr -s ' ' | cut -d ' ' -f2)
cpu_threads=$(lscpu | grep -e "^CPU(s):" | tr -s ' ' | cut -d ' ' -f2)
cpu_frequency=$(lscpu | grep "CPU MHz:" | tr -s ' ' | cut -d ' ' -f3) # caution, key contains space

memory_frequency=$(dmidecode -t 17 | grep "Speed:" | uniq | tr -s ' ' | cut -d ' ' -f2)
memory_size=$(free -m  | head -n 2 | tail -n 1 | tr -s ' ' | cut -d ' ' -f2) #MEGABYTE!

network_speed=$(ethtool ethdata | grep "Speed:" | tr -s ' ' | cut -d ' ' -f2)


# print hardware information
echo -ne "cpu_arch\t"
echo -ne "cpu_cores\t"
echo -ne "cpu_freq\t"

echo -ne "mem_freq\t"
echo -ne "mem_size\t"
echo -ne "netw_speed\n"


echo -ne $cpu_architecture"\t"
echo -ne $cpu_threads"\t"
echo -ne $cpu_frequency"\t"

echo -ne $memory_frequency"\t"
echo -ne $memory_size"\t"
echo -ne $network_speed"\n"


