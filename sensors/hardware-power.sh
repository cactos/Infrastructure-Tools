#!/bin/bash
isPowerSupply=false
psSerial=""
psCapacity=""

# print headers
echo -ne "serial\t"
echo -ne "capacity\n"

while IFS= read -r -d $'\n' line; do

	## when new line, new section starts. reset state.
	if [[ -z $line ]]; then
		# print
		if [[ ! -z $psSerial ]]; then
			echo -ne $psSerial"\t"
			echo -ne $psCapacity"\n"
		fi
		# reset
		isPowerSupply=false
		psSerial=""
		psCapacity=""
		# skip line, it's empty
		continue
	fi
	
	## read key/value pair from line
	rowKey=$(echo $line | cut -d ':' -f1)
	rowValue=$(echo $line | cut -d ':' -f2)

	## if we have a section title
	if [[ "$rowKey" == *"FRU Device Description"* ]]; then
		## look if new fru entry is for power supply
		if [[ $rowValue == *"PWR Supply"* || 
			$rowValue == *"PS "* || 
			$rowValue == *"Pwr Supply"* ]]
		then
			isPowerSupply=true
		fi
	fi
	
	## if we are in a power supply section, look for serial number
	if [[ $isPowerSupply == true ]]; then
		if [[ "$rowKey" == *"Serial"* ]]; then
			psSerial=$rowValue
		fi
	fi
	
	## if we are in a power supply section, look for product number
	if [[ $isPowerSupply == true ]]; then
		if [[ "$rowKey" == *"Name"* || "$rowKey" == *"Board Product"* ]]; then
			psCapacity=$(echo $(grep -o "[0-9]" <<<"$rowValue") | tr -d ' ')
		fi
	fi
	
done < <(ipmitool fru)