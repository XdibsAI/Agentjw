import sqlite3
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from decimal import Decimal
from enum import Enum
import threading

from config import Config

logger = logging.getLogger(__name__)

class TradeStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"

@dataclass
class Trade:
    id: Optional[int]
    token_address: str
    token_symbol: str
    side: str  # BUY or SELL
    amount: Decimal
    price: Decimal
    slippage: Decimal
    status: TradeStatus
    tx_hash: Optional[str]
    created_at: float
    updated_at: float
    strategy: str
    fees: Decimal
    realized_pnl: Optional[Decimal] = None

@dataclass
class Position:
    id: Optional[int]
    token_address: str
    token_symbol: str
    side: str  # LONG or SHORT
    amount: Decimal
    entry_price: Decimal
    status: PositionStatus
    created_at: float
    updated_at: float
    strategy: str

    token_amount: Optional[Decimal] = None
    entry_sol: Optional[Decimal] = None
    tx_hash: Optional[str] = None

    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None

@dataclass
class RiskMetrics:
    id: Optional[int]
    timestamp: float
    total_exposure: Decimal
    max_position_size: Decimal
    current_drawdown: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    sharpe_ratio: Decimal

class Database:
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
        
    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            # Create trades table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT,
                    side TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    price TEXT NOT NULL,
                    slippage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tx_hash TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    fees TEXT NOT NULL,
                    realized_pnl TEXT
                )
            """)
            
            # Create positions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT,
                    side TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    entry_price TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    stop_loss TEXT,
                    take_profit TEXT,
                    realized_pnl TEXT
                )
            """)
            
            # Create risk metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    total_exposure TEXT NOT NULL,
                    max_position_size TEXT NOT NULL,
                    current_drawdown TEXT NOT NULL,
                    win_rate TEXT NOT NULL,
                    profit_factor TEXT NOT NULL,
                    sharpe_ratio TEXT NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_token ON trades(token_address)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_token ON positions(token_address)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
            
            conn.commit()
            
    @contextmanager
    def _get_connection(self):
        """Get database connection with thread safety"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
                
    def save_trade(self, trade: Trade) -> int:
        """Save a trade to database"""
        with self._get_connection() as conn:
            if trade.id is None:
                # Insert new trade
                cursor = conn.execute("""
                    INSERT INTO trades (
                        token_address, token_symbol, side, amount, price, slippage,
                        status, tx_hash, created_at, updated_at, strategy, fees, realized_pnl
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.token_address,
                    trade.token_symbol,
                    trade.side,
                    str(trade.amount),
                    str(trade.price),
                    str(trade.slippage),
                    trade.status.value,
                    trade.tx_hash,
                    trade.created_at,
                    trade.updated_at,
                    trade.strategy,
                    str(trade.fees),
                    str(trade.realized_pnl) if trade.realized_pnl is not None else None
                ))
                trade_id = cursor.lastrowid
            else:
                # Update existing trade
                conn.execute("""
                    UPDATE trades SET
                        token_address = ?, token_symbol = ?, side = ?, amount = ?,
                        price = ?, slippage = ?, status = ?, tx_hash = ?,
                        updated_at = ?, strategy = ?, fees = ?, realized_pnl = ?
                    WHERE id = ?
                """, (
                    trade.token_address,
                    trade.token_symbol,
                    trade.side,
                    str(trade.amount),
                    str(trade.price),
                    str(trade.slippage),
                    trade.status.value,
                    trade.tx_hash,
                    trade.updated_at,
                    trade.strategy,
                    str(trade.fees),
                    str(trade.realized_pnl) if trade.realized_pnl is not None else None,
                    trade.id
                ))
                trade_id = trade.id
                
            conn.commit()
            logger.info(f"Saved trade {trade_id} for {trade.token_symbol}")
            return trade_id
            
    def get_trade(self, trade_id: int) -> Optional[Trade]:
        """Get a trade by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_trade(row)
            return None
            
    def get_trades_by_token(self, token_address: str, limit: int = 100) -> List[Trade]:
        """Get trades for a specific token"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM trades 
                WHERE token_address = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (token_address, limit))
            return [self._row_to_trade(row) for row in cursor.fetchall()]
            
    def get_trades_by_status(self, status: TradeStatus, limit: int = 100) -> List[Trade]:
        """Get trades by status"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM trades 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (status.value, limit))
            return [self._row_to_trade(row) for row in cursor.fetchall()]
            
    def get_recent_trades(self, hours: int = 24, limit: int = 100) -> List[Trade]:
        """Get recent trades within specified hours"""
        since = time.time() - (hours * 3600)
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM trades 
                WHERE created_at >= ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (since, limit))
            return [self._row_to_trade(row) for row in cursor.fetchall()]
            
    def save_position(self, position: Position) -> int:
        """Save a position to database"""
        with self._get_connection() as conn:
            if position.id is None:
                # Insert new position
                cursor = conn.execute("""
                    INSERT INTO positions (
                        token_address, token_symbol, side, amount, entry_price,
                        status, created_at, updated_at, strategy, token_amount, entry_sol, tx_hash,
                        stop_loss, take_profit, realized_pnl
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.token_address,
                    position.token_symbol,
                    position.side,
                    str(position.amount),
                    str(position.entry_price),
                    position.status.value,
                    position.created_at,
                    position.updated_at,
                    position.strategy,
                    str(position.token_amount) if position.token_amount is not None else None,
                    str(position.entry_sol) if position.entry_sol is not None else None,
                    position.tx_hash,
                    str(position.stop_loss) if position.stop_loss is not None else None,
                    str(position.take_profit) if position.take_profit is not None else None,
                    str(position.realized_pnl) if position.realized_pnl is not None else None
                ))
                position_id = cursor.lastrowid
            else:
                # Update existing position
                conn.execute("""
                    UPDATE positions SET
                        token_address = ?, token_symbol = ?, side = ?, amount = ?,
                        entry_price = ?, status = ?, updated_at = ?, strategy = ?,
                        token_amount = ?, entry_sol = ?, tx_hash = ?,
                        stop_loss = ?, take_profit = ?, realized_pnl = ?
                    WHERE id = ?
                """, (
                    position.token_address,
                    position.token_symbol,
                    position.side,
                    str(position.amount),
                    str(position.entry_price),
                    position.status.value,
                    position.updated_at,
                    position.strategy,
                    str(position.token_amount) if position.token_amount is not None else None,
                    str(position.entry_sol) if position.entry_sol is not None else None,
                    position.tx_hash,
                    str(position.stop_loss) if position.stop_loss is not None else None,
                    str(position.take_profit) if position.take_profit is not None else None,
                    str(position.realized_pnl) if position.realized_pnl is not None else None,
                    position.id
                ))
                position_id = position.id
                
            conn.commit()
            logger.info(f"Saved position {position_id} for {position.token_symbol}")
            return position_id
            
    def get_position(self, position_id: int) -> Optional[Position]:
        """Get a position by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_position(row)
            return None
            
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE status = ? 
                ORDER BY created_at DESC
            """, (PositionStatus.OPEN.value,))
            return [self._row_to_position(row) for row in cursor.fetchall()]
            
    def get_positions_by_token(self, token_address: str, limit: int = 100) -> List[Position]:
        """Get positions for a specific token"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE token_address = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (token_address, limit))
            return [self._row_to_position(row) for row in cursor.fetchall()]
            
    def get_recent_positions(self, hours: int = 24, limit: int = 100) -> List[Position]:
        """Get recent positions within specified hours"""
        since = time.time() - (hours * 3600)
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE created_at >= ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (since, limit))
            return [self._row_to_position(row) for row in cursor.fetchall()]
            
    def _row_to_position(self, row):
        return Position(
            id=row["id"],
            token_address=row["token_address"],
            token_symbol=row["token_symbol"],
            side=row["side"],
            amount=Decimal(str(row["amount"])),
            entry_price=Decimal(str(row["entry_price"])),
            status=PositionStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            strategy=row["strategy"],
            token_amount=Decimal(str(row["token_amount"])) if row["token_amount"] else None,
            entry_sol=Decimal(str(row["entry_sol"])) if row["entry_sol"] else None,
            tx_hash=row["tx_hash"],
            stop_loss=Decimal(str(row["stop_loss"])) if row["stop_loss"] else None,
            take_profit=Decimal(str(row["take_profit"])) if row["take_profit"] else None,
            realized_pnl=Decimal(str(row["realized_pnl"])) if row["realized_pnl"] else None,
        )

    def save_risk_metrics(self, metrics: RiskMetrics) -> int:
        """Save risk metrics to database"""
        with self._get_connection() as conn:
            if metrics.id is None:
                # Insert new metrics
                cursor = conn.execute("""
                    INSERT INTO risk_metrics (
                        timestamp, total_exposure, max_position_size, current_drawdown,
                        win_rate, profit_factor, sharpe_ratio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp,
                    str(metrics.total_exposure),
                    str(metrics.max_position_size),
                    str(metrics.current_drawdown),
                    str(metrics.win_rate),
                    str(metrics.profit_factor),
                    str(metrics.sharpe_ratio)
                ))
                metrics_id = cursor.lastrowid
            else:
                # Update existing metrics
                conn.execute("""
                    UPDATE risk_metrics SET
                        timestamp = ?, total_exposure = ?, max_position_size = ?,
                        current_drawdown = ?, win_rate = ?, profit_factor = ?,
                        sharpe_ratio = ?
                    WHERE id = ?
                """, (
                    metrics.timestamp,
                    str(metrics.total_exposure),
                    str(metrics.max_position_size),
                    str(metrics.current_drawdown),
                    str(metrics.win_rate),
                    str(metrics.profit_factor),
                    str(metrics.sharpe_ratio),
                    metrics.id
                ))
                metrics_id = metrics.id
                
            conn.commit()
            logger.info(f"Saved risk metrics {metrics_id}")
            return metrics_id
            
    def get_recent_risk_metrics(self, hours: int = 24, limit: int = 100) -> List[RiskMetrics]:
        """Get recent risk metrics within specified hours"""
        since = time.time() - (hours * 3600)
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM risk_metrics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (since, limit))
            return [self._row_to_risk_metrics(row) for row in cursor.fetchall()]
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        with self._get_connection() as conn:
            # Total trades
            cursor = conn.execute("SELECT COUNT(*) as total FROM trades")
            total_trades = cursor.fetchone()['total']
            
            # Successful trades
            cursor = conn.execute("""
                SELECT COUNT(*) as successful 
                FROM trades 
                WHERE status = ?
            """, (TradeStatus.FILLED.value,))
            successful_trades = cursor.fetchone()['successful']
            
            # Win rate
            win_rate = Decimal(successful_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')
            
            # Total PnL
            cursor = conn.execute("""
                SELECT SUM(CAST(realized_pnl AS REAL)) as total_pnl 
                FROM trades 
                WHERE realized_pnl IS NOT NULL
            """)
            total_pnl_row = cursor.fetchone()
            total_pnl = Decimal(total_pnl_row['total_pnl']) if total_pnl_row['total_pnl'] is not None else Decimal('0')
            
            # Open positions count
            cursor = conn.execute("""
                SELECT COUNT(*) as open_positions 
                FROM positions 
                WHERE status = ?
            """, (PositionStatus.OPEN.value,))
            open_positions = cursor.fetchone()['open_positions']
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'open_positions': open_positions
            }
            
    def get_token_performance(self, token_address: str) -> Dict[str, Any]:
        """Get performance metrics for a specific token"""
        with self._get_connection() as conn:
            # Token trades
            cursor = conn.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as successful
                FROM trades 
                WHERE token_address = ?
            """, (TradeStatus.FILLED.value, token_address))
            trade_stats = cursor.fetchone()
            
            # Token PnL
            cursor = conn.execute("""
                SELECT SUM(CAST(realized_pnl AS REAL)) as total_pnl 
                FROM trades 
                WHERE token_address = ? AND realized_pnl IS NOT NULL
            """, (token_address,))
            pnl_row = cursor.fetchone()
            
            # Current position
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE token_address = ? AND status = ?
                ORDER BY created_at DESC 
                LIMIT 1
            """, (token_address, PositionStatus.OPEN.value))
            position_row = cursor.fetchone()
            
            return {
                'total_trades': trade_stats['total'] or 0,
                'successful_trades': trade_stats['successful'] or 0,
                'win_rate': Decimal(trade_stats['successful'] or 0) / Decimal(trade_stats['total'] or 1),
                'total_pnl': Decimal(pnl_row['total_pnl']) if pnl_row['total_pnl'] is not None else Decimal('0'),
                'current_position': self._row_to_position(position_row) if position_row else None
            }
            
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to prevent database bloat"""
        cutoff = time.time() - (days * 24 * 3600)
        with self._get_connection() as conn:
            # Clean up old trades (keep filled trades for longer)
            conn.execute("""
                DELETE FROM trades 
                WHERE created_at < ? AND status != ?
            """, (cutoff, TradeStatus.FILLED.value))
            
            # Clean up old positions (keep open positions)
            conn.execute("""
                DELETE FROM positions 
                WHERE created_at < ? AND status != ?
            """, (cutoff, PositionStatus.OPEN.value))
            
            # Clean up old risk metrics
            conn.execute("""
                DELETE FROM risk_metrics 
                WHERE timestamp < ?
            """, (cutoff,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
    def sync_paper_balance_after_sell(self, token_address: str, sell_amount: Decimal, sell_price: Decimal):
        """Sync paper balance after a sell trade by reducing the position amount"""
        with self._get_connection() as conn:
            # Get the current open position for this token
            cursor = conn.execute("""
                SELECT * FROM positions 
                WHERE token_address = ? AND status = ?
                ORDER BY created_at DESC 
                LIMIT 1
            """, (token_address, PositionStatus.OPEN.value))
            
            row = cursor.fetchone()
            if row:
                position = self._row_to_position(row)
                
                # Reduce the position amount by the sold amount
                new_amount = position.amount - sell_amount
                
                # If position is fully closed, mark as closed
                if new_amount <= 0:
                    new_status = PositionStatus.CLOSED.value
                    new_amount = Decimal('0')
                else:
                    new_status = position.status.value
                    
                # Update the position
                conn.execute("""
                    UPDATE positions SET
                        amount = ?,
                        status = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    str(new_amount),
                    new_status,
                    time.time(),
                    position.id
                ))
                
                conn.commit()
                logger.info(f"Synced paper balance for {position.token_symbol}: reduced position by {sell_amount}")