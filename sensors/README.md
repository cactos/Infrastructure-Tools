 
# Currently used 

## VM level

### From Diagnostics API

 * ResidingMemory
 * AllocatedMemory
 * vCores amount
 * vCores utilisation
 * libvirtId -> UUID mapping
 
## PM level

### From Sigar SystemMetrics

## Initial Adaptors

```
add ExecAdaptor Df 60 /bin/df -P -h 0
add org.apache.hadoop.chukwa.datacollection.adaptor.sigar.SystemMetrics SystemMetrics 10 0 0
add ExecAdaptor VirtTop 60 virt-top -b -c qemu:///system --script --csv /dev/stdout -n 2 0
add ExecAdaptor Ipmi 60 sudo ipmi-oem intelnm get-node-manager-statistics 0
```

Example output:

```
/bin/df -P -h
Filesystem                     Size  Used Avail Use% Mounted on
/dev/mapper/vg_system-lv_root  229G   19G  201G   9% /
devtmpfs                        48G     0   48G   0% /dev
tmpfs                           48G     0   48G   0% /dev/shm
tmpfs                           48G   41M   48G   1% /run
tmpfs                           48G     0   48G   0% /sys/fs/cgroup
/dev/md0                       488M  167M  292M  37% /boot

virt-top -b -c qemu:///system --script --csv /dev/stdout -n 2
Hostname,Time,Arch,Physical CPUs,Count,Running,Blocked,Paused,Shutdown,Shutoff,Crashed,Active,Inactive,%CPU,Total hardware memory (KB),Total memory (KB),Total guest memory (KB),Total CPU time (ns),Domain ID,Domain name,CPU (ns),%CPU,Mem (bytes),%Mem,Block RDRQ,Block WRRQ,Net RXBY,Net TXBY
computenode18,12:44:42,x86_64,16,1,1,0,0,0,0,0,1,0,0.0,98822656,8388608,8388608,0,3,instance-00000077,0.,0.,0,0,,,,
computenode18,12:44:45,x86_64,16,1,1,0,0,0,0,0,1,0,0.0,98822656,8388608,8388608,0,3,instance-00000077,0.,0.,8388608,8,0,0,0,0
```

# Metrics Needed for CACTOS Models

## VM level

 * Amount of CPUs
 * Amount of Memory
 * Memory utilisation
 * CPU utilisation
 * Disk Read/Write throughput (??)
 * Network Utilisation
  
## PM level

 * Power Supply
 * Power Capacity Limit
 * Network Interconnects
 * CPU amount of cores, frequency, architecture, turbo-mode
 * Memory Size, read/write bandwidth
 * Storage Size, read/write delay, read/write bandwidth
 
 * Memory utilisation %
 * Storage read/write throughput, utilisation
 * Network throughput
 
# Useful Metrics

## Physical Machine 

 * hostname

### CPU

 * architecture
 * cores
 * max. frequency
 how to query:
 lscpu
 
 * user utilisation
 * system utilisation
 * wio
 

### MEMORY

 * totel size
 * frequency 
 how to query:
 dmidecode --type 17
 
 * used
 
 
### NETWORK (DATA-IF ONLY)

 * Speed
 
 how to query:
 ethtool ethdata
 
### DISK (FOR VM-USAGE ONLY)
 
 * Size 
 how to query:
 df -h
 
## Physical Machine Load

 
# New Mapping

https://docs.google.com/spreadsheets/d/1nDYYpv5r2IEHPKYFb74QoOjOsqpqCJWLhfHP49-eqzQ/edit?usp=sharing
 
# VM Measurement

virsh list --all --name # optional, to get libvirt name
virsh list --all --uuid # to get openstack id
virsh list --all # to get state!

virsh domblklist instance-00000077
Target     Source
------------------------------------------------
vda        /var/lib/nova/instances/6acd063e-fa11-4262-b822-a168ad9276ff/disk

virsh domblkinfo instance-00000077 vda
Capacity:       85899345920
Allocation:     233447424
Physical:       233447424

