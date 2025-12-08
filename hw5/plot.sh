#!/bin/bash

#check for installation of parallel-rsync

if [ "$#" -ne 1 ] ; then
	echo "Data file not supplied."
	echo "Usage ./plot {data-file.txt}"
	exit
fi

gnuplot -e "filename='$1'" graph.gnuplot
mv graph.png $1.png
# xdg-open graph.png
