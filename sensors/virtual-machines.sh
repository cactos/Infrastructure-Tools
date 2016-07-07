#!/bin/bash

echo -ne "vm_name\t"
echo -ne "vm_uuid\t"
echo -ne "vm_image_uuid\t"
echo -ne "vm_tenant_uuid\t"
echo -ne "vm_state\n"

while IFS= read -r -d $'\n' line; do
        arr=( $(echo $line) )

        vm_name=$(virsh dominfo ${arr[0]} | grep "Name:" | tr -s ' ' | cut -d ' ' -f2)
        vm_uuid=$(virsh dominfo ${arr[0]} | grep "UUID:" | tr -s ' ' | cut -d ' ' -f2)
        vm_image_uuid=$(virsh dumpxml ${arr[0]} | grep "image" | tr -s ' '| cut -f4 -d'"')
        vm_tenant_uuid=$(virsh dumpxml ${arr[0]} | grep "project" | cut -f2 -d '"')
        vm_state=$(virsh dominfo ${arr[0]} | grep "State:" | tr -s ' ' | cut -d ' ' -f2)

        # print fields
        echo -ne $vm_name"\t"
        echo -ne $vm_uuid"\t"
        echo -ne $vm_image_uuid"\t"
        echo -ne $vm_tenant_uuid"\t"
        echo -ne $vm_state"\t"
        echo -ne "\n"

done < <(virsh list --all | tail -n+3 | awk '{print $2}'| awk NF)