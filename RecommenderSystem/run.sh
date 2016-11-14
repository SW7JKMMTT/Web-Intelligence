#!/bin/bash

for i in $(seq 5 5 100); do
    for t_d in $(seq 2 9); do
        t="0.$t_d"
        python3 main.py -k $i -t $t > run-${i}-${t_d}.txt
    done 
done
