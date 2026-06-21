from pathlib import Path

p = Path("strategy.py")
s = p.read_text()

# tambah import json
if "import json" not in s:
    s = s.replace(
        "import asyncio",
        "import asyncio\nimport json\nfrom pathlib import Path"
    )

# tambah helper sebelum class pertama
marker = "class "

helper = '''
PAPER_WALLET_FILE = Path(__file__).parent / "paper_wallet.json"

def load_paper_balance():
    try:
        if PAPER_WALLET_FILE.exists():
            data = json.loads(PAPER_WALLET_FILE.read_text())
            return float(data.get("balance", 10.0))
    except Exception:
        pass
    return 10.0

def save_paper_balance(balance):
    PAPER_WALLET_FILE.write_text(
        json.dumps(
            {
                "balance": round(balance, 6),
                "updated": time.time()
            },
            indent=2
        )
    )

'''

if "PAPER_WALLET_FILE" not in s:
    s = s.replace(marker, helper + marker, 1)

# replace init
s = s.replace(
    "self.paper_balance = 10.0",
    "self.paper_balance = load_paper_balance()"
)

# BUY save
s = s.replace(
    "self.paper_balance -= sol_amount\n\n            logger.info(",
    "self.paper_balance -= sol_amount\n            save_paper_balance(self.paper_balance)\n\n            logger.info("
)

# SELL save
s = s.replace(
    "self.paper_balance += sell_return\n\n            logger.info(",
    "self.paper_balance += sell_return\n            save_paper_balance(self.paper_balance)\n\n            logger.info("
)

p.write_text(s)