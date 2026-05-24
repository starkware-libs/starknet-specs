---
name: install-starknet-mcp
description: Install and configure the Starknet MCP server for Claude Code
allowed-tools: Bash, Read
argument-hint: "<rpc-url>"
---

# Install Starknet MCP Server

Set up the Starknet MCP server so Claude can query a live Starknet node.

## Steps

1. The user should provide their Starknet JSON-RPC endpoint URL as `$ARGUMENTS`. If no argument was given, ask the user for their RPC URL. It must be a v0.10.2+ endpoint.

2. Install the Python dependencies:

   ```bash
   pip install -r mcp/requirements.txt
   ```

3. Ask the user which scope they want:

   - **Global** (`--scope user`) — available in all projects. Best if they work with Starknet across multiple repos. Requires using the absolute path to `mcp/server.py`.
   - **Project** (default) — available only in this repo. Uses a relative path.

4. Register the MCP server with Claude Code using the chosen scope. Note that `--env` must come **before** `--` so Claude sets it in the server's environment (anything after `--` is passed as argv to the server itself):

   - Global: `claude mcp add --scope user --env STARKNET_RPC_URL=<the-url> starknet -- python <absolute-path-to-server.py>`
   - Project: `claude mcp add --env STARKNET_RPC_URL=<the-url> starknet -- python mcp/server.py`

5. Verify the server is registered by running:

   ```bash
   claude mcp list
   ```

6. Tell the user the installation is complete and they should restart Claude Code for the new MCP server to take effect. List a few example prompts they can try:
   - "What's the latest block number on Starknet?"
   - "Get me the transaction receipt for 0x..."
   - "What's the ETH token total supply on Starknet?"
