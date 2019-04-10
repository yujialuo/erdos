#!/bin/bash

echo "Active Replication Test Starts:"

for i  in {1..5}; do
   python active_replication/flux_test.py --framework=ros --fail_time=i
done