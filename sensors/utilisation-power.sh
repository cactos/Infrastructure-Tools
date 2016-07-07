#!/bin/bash

# printing headers
echo "consumption"

# collect power data
consumption="-" # Watts consumed
powerIntel=$(ipmi-oem intelnm get-node-manager-statistics 2>&1 | grep "Current Power")
if [ "$powerIntel" == "" ]; then
        powerDell=$(ipmi-oem dell get-power-consumption-statistics average | grep "Last Minute Average Power")
	if [ "$powerDell" == "" ]; then
		consumption="-"
	else
		consumption=$(echo $powerDell | cut -d ':' -f2)
		#capacity=$(ipmi-oem dell power-supply-info | grep "Rated Watts" | cut -d ':' -f2 | cut -d ' ' -f 2)
	fi
else
        consumption=$(echo $powerIntel | cut -d ':' -f2)
fi

# print collected data
echo -ne $consumption | cut -d ' ' -f1
echo -ne "\n"
