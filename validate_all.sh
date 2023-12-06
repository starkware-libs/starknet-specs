#!/bin/bash

set -u

failure_count=0

for spec_file in "api/starknet_api_openrpc.json" "api/starknet_trace_api_openrpc.json" "api/starknet_write_api.json"; do
    node validate.js $spec_file || failure_count=$((failure_count + 1))
done

exit failure_count
