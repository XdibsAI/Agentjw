import os
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich import box
import asyncio
import json
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import Transaction
import base58
import time
from datetime import datetime

load_dotenv()

class Config:
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    IS_PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    # Solana RPC
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    SOLANA_WS_URL = os.getenv('SOLANA_WS_URL', 'wss://api.mainnet-beta.solana.com')
    
    # Wallet
    WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY')
    WALLET_PUBLIC_KEY = os.getenv('WALLET_PUBLIC_KEY')

class Dashboard:
    def __init__(self):
        self.console = Console()
        self.client = AsyncClient(Config.SOLANA_RPC_URL)
        self.wallet = self._init_wallet()
        self.positions = []
        self.pnl = 0.0
        self.recent_trades = []
        self.bot_status = "Running"
        self.last_update = time.time()
        self.paper_balance = 1000.0  # Initial paper balance for paper trading
        
    def _init_wallet(self):
        if Config.WALLET_PRIVATE_KEY:
            try:
                key_bytes = base58.b58decode(Config.WALLET_PRIVATE_KEY)
                return Keypair.from_secret_key(key_bytes)
            except:
                self.console.print("[red]Invalid private key in config[/red]")
                return None
        elif Config.WALLET_PUBLIC_KEY:
            try:
                return PublicKey(Config.WALLET_PUBLIC_KEY)
            except:
                self.console.print("[red]Invalid public key in config[/red]")
                return None
        else:
            self.console.print("[yellow]No wallet configured[/yellow]")
            return None

    async def get_sol_balance(self):
        if not self.wallet:
            return 0.0
        try:
            if isinstance(self.wallet, Keypair):
                pubkey = self.wallet.public_key
            else:
                pubkey = self.wallet
                
            balance = await self.client.get_balance(pubkey)
            return balance['result']['value'] / 1_000_000_000  # Convert lamports to SOL
        except Exception as e:
            self.console.print(f"[red]Error fetching balance: {e}[/red]")
            return 0.0

    def sync_paper_balance_after_sell(self, sold_amount_usd: float, token_amount: float = 0, token_name: str = ""):
        """Sync paper balance after a sell operation in paper trading mode"""
        if Config.IS_PAPER_TRADING:
            self.paper_balance += sold_amount_usd
            self.console.print(f"[green]Paper balance updated: ${self.paper_balance:.2f} (+${sold_amount_usd:.2f})[/green]")
            # Log the sell transaction
            if token_amount > 0 and token_name:
                self.recent_trades.insert(0, {
                    "time": datetime.now().strftime('%H:%M:%S'),
                    "token": token_name,
                    "type": "SELL",
                    "amount": str(token_amount),
                    "price": f"${sold_amount_usd/token_amount:.6f}" if token_amount > 0 else "N/A"
                })
                # Keep only last 10 trades
                self.recent_trades = self.recent_trades[:10]

async def _close_position(self, position_data):
    """Close position and update balance"""
    # Existing logic here...
    sold_amount_usd = 100.0  # Example value
    token_amount = 1000.0    # Example value
    token_name = "TEST"      # Example value
    
    # Trailing stop buffer 2% - only for trace function
    if hasattr(self, 'trace') and callable(self.trace):
        # Apply 2% buffer to sold amount
        buffer_amount = sold_amount_usd * 0.02
        sold_amount_usd = sold_amount_usd - buffer_amount
    
    # Update balance after SELL
    if Config.IS_PAPER_TRADING:
        self.sync_paper_balance_after_sell(sold_amount_usd, token_amount, token_name)
    # For live trading, you would update the actual wallet balance here
    
    return {"status": "closed"}

    def execute_stop_loss(self, position):
        """Execute stop loss and update balance"""
        # Existing logic here...
        sold_amount_usd = 50.0   # Example value
        token_amount = 500.0     # Example value
        token_name = "TEST"      # Example value
        
        # Update balance after SELL
        if Config.IS_PAPER_TRADING:
            self.sync_paper_balance_after_sell(sold_amount_usd, token_amount, token_name)
        # For live trading, you would update the actual wallet balance here
        
        return {"status": "stop_loss_executed"}

    def execute_take_profit(self, position):
        """Execute take profit and update balance"""
        # Existing logic here...
        sold_amount_usd = 150.0  # Example value
        token_amount = 1500.0    # Example value
        token_name = "TEST"      # Example value
        
        # Update balance after SELL
        if Config.IS_PAPER_TRADING:
            self.sync_paper_balance_after_sell(sold_amount_usd, token_amount, token_name)
        # For live trading, you would update the actual wallet balance here
        
        return {"status": "take_profit_executed"}

    def create_wallet_panel(self, balance):
        content = f"SOL Balance: {balance:.4f} SOL"
        if Config.IS_PAPER_TRADING:
            content += f"\nPaper Balance: ${self.paper_balance:.2f}"
            content += "\n[yellow]PAPER TRADING MODE[/yellow]"
        return Panel(content, title="Wallet", border_style="green")

    def create_positions_table(self):
        table = Table(box=box.SIMPLE)
        table.add_column("Token", style="cyan")
        table.add_column("Amount", justify="right")
        table.add_column("Entry Price", justify="right")
        table.add_column("Current Price", justify="right")
        table.add_column("PnL", justify="right")
        
        # Sample positions - in real implementation, this would come from your trading logic
        sample_positions = [
            {"token": "BONK", "amount": "1000000", "entry": "0.000023", "current": "0.000025", "pnl": "+8.7%"},
            {"token": "WIF", "amount": "500", "entry": "1.24", "current": "1.32", "pnl": "+6.5%"},
        ]
        
        for pos in sample_positions:
            table.add_row(
                pos["token"],
                pos["amount"],
                pos["entry"],
                pos["current"],
                pos["pnl"]
            )
            
        return Panel(table, title="Open Positions")

    def create_pnl_panel(self):
        content = f"Daily PnL: [green]+{self.pnl:.2f}%[/green]" if self.pnl >= 0 else f"Daily PnL: [red]{self.pnl:.2f}%[/red]"
        return Panel(content, title="Performance", border_style="blue")

    def create_trades_table(self):
        table = Table(box=box.SIMPLE)
        table.add_column("Time", style="dim")
        table.add_column("Token", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Amount", justify="right")
        table.add_column("Price", justify="right")
        
        # Sample trades - in real implementation, this would come from your trading logic
        sample_trades = [
            {"time": "10:30:25", "token": "BONK", "type": "BUY", "amount": "500000", "price": "0.000023"},
            {"time": "09:45:12", "token": "WIF", "type": "BUY", "amount": "250", "price": "1.24"},
            {"time": "08:15:47", "token": "SOL", "type": "SELL", "amount": "0.5", "price": "98.45"},
        ]
        
        # Use actual recent trades if available
        trades_to_show = self.recent_trades if self.recent_trades else sample_trades
        
        for trade in trades_to_show:
            style = "green" if trade["type"] == "BUY" else "red"
            table.add_row(
                trade["time"],
                trade["token"],
                f"[{style}]{trade['type']}[/{style}]",
                trade["amount"],
                trade["price"]
            )
            
        return Panel(table, title="Recent Trades")

    def create_status_panel(self):
        status_color = "green" if self.bot_status == "Running" else "red"
        content = f"Status: [{status_color}]{self.bot_status}[/{status_color}]\n"
        content += f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
        return Panel(content, title="Bot Status", border_style="yellow")

    def create_layout(self, balance):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="wallet"),
            Layout(name="positions")
        )
        
        layout["right"].split_column(
            Layout(name="pnl"),
            Layout(name="trades")
        )
        
        # Update components
        layout["header"].update(Panel(Align.center("[bold blue]Solana Meme Trading Bot[/bold blue]", vertical="middle")))
        layout["wallet"].update(self.create_wallet_panel(balance))
        layout["positions"].update(self.create_positions_table())
        layout["pnl"].update(self.create_pnl_panel())
        layout["trades"].update(self.create_trades_table())
        layout["footer"].update(self.create_status_panel())
        
        return layout

    async def run(self):
        with Live(self.create_layout(0), refresh_per_second=1, screen=True) as live:
            while True:
                try:
                    balance = await self.get_sol_balance()
                    layout = self.create_layout(balance)
                    live.update(layout)
                    await asyncio.sleep(5)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error updating dashboard: {e}[/red]")
                    await asyncio.sleep(5)

if __name__ == "__main__":
    dashboard = Dashboard()
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        print("\nDashboard stopped")