# StarkNet Specifications

This repository publishes different technical specifications pertaining to the implementation and interaction with StarkNet.

## API

The JSON-RPC API can be found under the `api/` folder.
You can view it more conveiently using the OpenRPC playground [here](https://playground.open-rpc.org/?uiSchema%5BappBar%5D%5Bui:splitView%5D=false&schemaUrl=https://raw.githubusercontent.com/starkware-libs/starknet-specs/master/api/starknet_api_openrpc.json&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:darkMode%5D=true&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false).

A guide to the API can be found [here](./starknet_vs_ethereum_node_apis.md).

# Tooling

When developing the schema, you can validate the OpenRPC schema file, by running the provided script.
Note this requires node.js installed.

The command:
```
./validate.js api/starknet_api_openrpc.json
```

will run a validation on the `api/starknet_api_openrpc.json` schema file.
If everything is ok, an appropriate message is displayed; otherwise errors are output to standard error.
