#!/bin/bash
#set -x

# GLOBAL CONF VARIABLES
HA_URL="http://playgen:D%40taP1aY@134.60.64.186:2182/;csv"
SLEEP=10
#HA_GROUP="gamification" 
HA_GROUP="masters"

function getValues(){
	csv=$(curl -X GET --silent "$HA_URL")
	gamification_backend=$(echo "$csv" | grep "$HA_GROUP,BACKEND,")
	stot=$(echo "$gamification_backend" | cut -d',' -f8)
	hrsp_2xx=$(echo "$gamification_backend" | cut -d',' -f41)
	echo $stot $hrsp_2xx
}

OLD_VALUES=()
while true 
do
	loop_start=$(($(date +%s%N))) #ns

	new_values=($(getValues))
	
	if [[ ! -z $OLD_VALUES ]]; then
		stot_new=${new_values[0]}
		stot_old=${OLD_VALUES[0]}
		echo -ne $(date +%s)" "
		echo -ne ${new_values[@]}" -> "
		stot_diff=$(echo "($stot_new-$stot_old)/$SLEEP" | bc -l) #TODO replace SLEEP with the actual spent time
		echo -ne $stot_diff
		echo -ne "\n"
	fi
	
	OLD_VALUES=(${new_values[@]})
	

	# calculate rest of sleep time 
	loop_end=$(($(date +%s%N))) #ns
	loop_duration=$(echo "($loop_end-$loop_start)/1000000000" | bc -l)
	sleep_diff=$(echo "$SLEEP-$loop_duration" | bc -l)
	sleep $sleep_diff
done
