#!/bin/bash
# ============================================================
# AgentJW GOD MODE Upgrade Script
# Run: bash upgrade_godmode.sh
# ============================================================
set -e
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════╗"
echo "║  AgentJW → GOD MODE Upgrade             ║"
echo -e "╚══════════════════════════════════════════╝${NC}"

# Make sure we're in agentjw dir
cd ~/agentjw

echo -e "${CYAN}[1/4] Activating venv...${NC}"
source venv/bin/activate

echo -e "${CYAN}[2/4] Creating new directories...${NC}"
mkdir -p tools/trading tools/youtube tools/project_manager
mkdir -p agents/specialist memory/projects_db

echo -e "${CYAN}[3/4] Verifying all files present...${NC}"
REQUIRED=(
    "core/models.py"
    "memory/memory_store.py"
    "tools/project_manager/manager.py"
    "tools/trading/trading_tool.py"
    "tools/youtube/youtube_tool.py"
    "agents/specialist/repair_specialist.py"
    "agents/orchestrator.py"
    "interface/cli.py"
)
ALL_OK=true
for f in "${REQUIRED[@]}"; do
    if [ -f "$f" ]; then
        echo -e "  ${GREEN}✓ $f${NC}"
    else
        echo -e "  ${YELLOW}✗ MISSING: $f${NC}"
        ALL_OK=false
    fi
done

echo -e "${CYAN}[4/4] Creating __init__.py files...${NC}"
touch tools/trading/__init__.py
touch tools/youtube/__init__.py
touch tools/project_manager/__init__.py
touch agents/specialist/__init__.py

echo ""
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════╗"
    echo "║  ✅ GOD MODE Upgrade Complete!           ║"
    echo -e "╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "Run: agentjw"
    echo ""
    echo -e "${CYAN}New Commands:${NC}"
    echo "  build trading bot for binance BTC/USDT scalping"
    echo "  build youtube auto upload tool"
    echo "  projects         - see all projects"
    echo "  repair <id>      - auto-repair a project"
    echo "  analyze <id>     - analyze trading strategy"
    echo "  continue <id>    - resume a project"
    echo "  worklog          - see work history"
else
    echo -e "${YELLOW}⚠️  Some files missing. Re-upload agentjw.tar.gz and extract.${NC}"
fi
