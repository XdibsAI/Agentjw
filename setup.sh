#!/bin/bash
# ============================================================
# AgentJW - Complete VPS Setup Script
# Run: bash setup.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║     🤖  AgentJW - VPS Setup Script              ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Check Python ──────────────────────────────────────────
echo -e "${CYAN}[1/6] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 not found. Installing...${NC}"
    apt-get update -qq && apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# ── Check pip ─────────────────────────────────────────────
echo -e "${CYAN}[2/6] Checking pip...${NC}"
if ! command -v pip3 &> /dev/null; then
    apt-get install -y python3-pip
fi
echo -e "${GREEN}✓ pip ready${NC}"

# ── Create virtual environment ────────────────────────────
echo -e "${CYAN}[3/6] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ venv created${NC}"
else
    echo -e "${GREEN}✓ venv already exists${NC}"
fi

# ── Activate venv ─────────────────────────────────────────
source venv/bin/activate
echo -e "${GREEN}✓ venv activated${NC}"

# ── Install dependencies ──────────────────────────────────
echo -e "${CYAN}[4/6] Installing Python dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ── Create .env if not exists ─────────────────────────────
echo -e "${CYAN}[5/6] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Created .env from .env.example${NC}"
    echo ""
    echo -e "${YELLOW}ACTION REQUIRED: Edit .env and add your API key:${NC}"
    echo -e "  ${GREEN}nano .env${NC}"
    echo ""
    echo "  For OpenAI:    OPENAI_API_KEY=sk-your-key"
    echo "  For Anthropic: ANTHROPIC_API_KEY=sk-ant-your-key"
    echo "                 LLM_PROVIDER=anthropic"
    echo ""
else
    echo -e "${GREEN}✓ .env already configured${NC}"
fi

# ── Create directories ────────────────────────────────────
echo -e "${CYAN}[6/6] Creating runtime directories...${NC}"
mkdir -p logs projects runtime/sandbox memory/chroma_db extensions/.versions
echo -e "${GREEN}✓ Directories created${NC}"

# ── Create run script ─────────────────────────────────────
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python main.py "$@"
EOF
chmod +x run.sh

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo "║           ✅ Setup Complete!                    ║"
echo "╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. Add your API key to .env:    nano .env"
echo "  2. Run AgentJW:                 ./run.sh"
echo "  3. Or activate venv manually:   source venv/bin/activate && python main.py"
echo ""
echo -e "${CYAN}Quick commands once running:${NC}"
echo "  build <task>    - Build a project autonomously"
echo "  build+ <task>   - Build with swarm intelligence"
echo "  help            - Show all commands"
echo ""
