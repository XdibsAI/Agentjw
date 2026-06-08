#!/bin/bash
set -e
GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
cd ~/agentjw && source venv/bin/activate

echo -e "${CYAN}[1/4] Creating directories...${NC}"
mkdir -p mcp/servers mcp/tools agents/workflow
touch mcp/__init__.py mcp/servers/__init__.py mcp/tools/__init__.py agents/workflow/__init__.py

echo -e "${CYAN}[2/4] Installing MCP dependencies...${NC}"
pip install fastapi uvicorn --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${CYAN}[3/4] Verifying all modules...${NC}"
python3 -c "
import sys; sys.path.insert(0,'.')
from agents.workflow.agent_dialog import agent_dialog; print('  ✓ AgentDialog')
from agents.workflow.agent_runner import agent_runner; print('  ✓ AgentRunner')
from agents.workflow.workflow_engine import workflow_engine; print('  ✓ WorkflowEngine')
from mcp.mcp_client import mcp_client; print(f'  ✓ MCP Client ({len(mcp_client.tools)} tools)')
from mcp.servers.gusmcp_server import gusmcp_server; print(f'  ✓ Gusmcp Server ({len(gusmcp_server.tools)} tools)')
from agents.orchestrator import orchestrator; print('  ✓ Orchestrator')
print()
print('  ✅ ALL SYSTEMS GO')
"

echo -e "${CYAN}[4/4] Done!${NC}"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗"
echo "║  ✅ MCP + Workflow Upgrade Complete!    ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""
echo "New commands:"
echo "  mcp tools              - list all MCP tools"
echo "  mcp servers            - list external MCP servers"
echo "  mcp add <name> <url>   - add external MCP server"
echo "  check token <address>  - check Solana token safety"
echo "  mcp <request>          - use MCP tools directly"
echo "  gusmcp                 - start Gusmcp HTTP server on :8765"
echo ""
echo "Workflow now active for all build commands!"
