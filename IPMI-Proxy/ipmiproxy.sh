#!/bin/bash

LOCAL_IP="<ip>"
port=51113
TIMEOUT=2
auth_token="<password>"


function ipmiproxy_server () {
    while true ; do
        read token action host # blocking until new input is received
	host=$(echo $host|tr -d '\n' | tr -d '\r') # remove new line at the end
	if [[ $token == "" || $token != $auth_token ]]; then
		echo "refusing invalid token" >&2
		continue
	fi
	echo "incoming request: "$action $host >&2
	IPMI_USER=`grep -E "$host.*enabled" ./accesslist | tr -s " " | cut -f2 -d" "`
	IPMI_PASS=`grep -E "$host.*enabled" ./accesslist | tr -s " " | cut -f3 -d" "`
	if [[ $IPMI_USER == "" ]]; then
		# skip when no IPMI credentials are found
		continue
	fi
        case $action in
            status )
		ssh computenode02 ipmitool -I lanplus -H ipmi.$host -U $IPMI_USER -P $IPMI_PASS chassis power status
		;;
            on )
                ssh computenode02 ipmitool -I lanplus -H ipmi.$host -U $IPMI_USER -P $IPMI_PASS chassis power on
		;;
            off)
                ssh computenode02 ipmitool -I lanplus -H ipmi.$host -U $IPMI_USER -P $IPMI_PASS chassis power soft
		;;
        esac
    done
}

# grab ctrl-c
trap ctrl_c INT
function ctrl_c() {
        echo "** Trapped CTRL-C"
	# Remove Open Port
	sudo iptables -D INPUT ! --source <subnet> --destination $LOCAL_IP --protocol tcp --dport $port -j DROP
	sudo iptables -D INPUT --source <subnet> --destination $LOCAL_IP --protocol tcp --dport $port  -j ACCEPT
}

# Open Port in iptables
sudo iptables -I INPUT ! --source <subnet> --destination $LOCAL_IP --protocol tcp --dport $port -j DROP
sudo iptables -I INPUT --source <subnet> --destination $LOCAL_IP --protocol tcp --dport $port -j ACCEPT


# Start ipmiproxy_server as a background coprocess named PROXY
# Its stdin filehandle is ${PROXY[1]}, and its stdout is ${PROXY[0]}
coproc PROXY { ipmiproxy_server; }

# Start a netcat server, with its stdin redirected from PROXY's stdout,
# and its stdout redirected to PROXY's stdin
echo "Start listening on port "$port
nc -w $TIMEOUT -l $port -k <&${PROXY[0]} >&${PROXY[1]}
