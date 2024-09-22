# Starknet Specifications

This repository publishes different technical specifications pertaining to the implementation of and interaction with Starknet.

## API

The JSON-RPC API can be found under the `api/` folder.
You can view it more conveniently using the OpenRPC playground [here](https://playground.open-rpc.org/?uiSchema%5BappBar%5D%5Bui:splitView%5D=false&schemaUrl=https://raw.githubusercontent.com/starkware-libs/starknet-specs/master/api/starknet_api_openrpc.json&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:darkMode%5D=true&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false).

A guide to the API can be found [here](./starknet_vs_ethereum_node_apis.md).

# Tooling

When developing the schema, you can validate the OpenRPC schema file, by running the provided script.
Note that this requires node.js be installed.

The follwoing command runs a validation on the `api/starknet_api_openrpc.json` schema file:
```
./validate.js api/starknet_api_openrpc.json
```


If everything is OK, an appropriate message is displayed. Otherwise, errors are output to standard error.
