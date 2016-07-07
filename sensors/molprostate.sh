#!/bin/bash
echo "MolproState"
if [ `pgrep "molpro"` ]; then
	echo "running"
else
	echo "stopped"
fi