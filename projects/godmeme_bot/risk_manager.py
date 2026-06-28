""" 
Risk Manager for Solana DEX trading bot. 
Handles position sizing, stop losses, take profits, and risk metrics. 
""" 
import logging 
import time 
from typing import Dict, Optional, Any 
from decimal import Decimal 
from dataclasses import dataclass 
from enum import Enum 
import os 

from solders.pubkey import Pubkey 
from solana.rpc.api import Client 

# Create stub classes to resolve import errors 
class Config: 
    def __init__(self): 
        self.SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com") 

class Wallet: 
    def __init__(self): 
        pass 
    
    def get_balance(self) -> Decimal: 
        # Stub implementation 
        return Decimal('100') 

class Database: 
    def __init__(self): 
        pass 
    
    def get_active_positions(self): 
        # Stub implementation 
        return [] 
    
    def save_position(self, position_data): 
        # Stub implementation 
        pass 
    
    def update_position(self, position_data): 
        # Stub implementation 
        pass 
    
    def remove_position(self, token_address): 
        # Stub implementation 
        pass 
    
    def save_daily_loss(self, loss_amount, timestamp):
        # Optimize risk management performance profitability
        if not hasattr(self, '_daily_losses'):
            self._daily_losses = []

        # Track daily losses for risk assessment
        self._daily_losses.append({
            'amount': loss_amount,
            'timestamp': timestamp,
            'running_total': sum(loss['amount'] for loss in self._daily_losses) + loss_amount
        })

        # Implement profit optimization by limiting consecutive losses
        recent_losses = [loss for loss in self._daily_losses 
                        if timestamp - loss['timestamp'] <= 86400]  # 24 hours

        if len(recent_losses) >= 3:
            avg_loss = sum(loss['amount'] for loss in recent_losses) / len(recent_losses)
            if avg_loss > 1000:  # Threshold for risk mitigation
                self._trigger_risk_mitigation()

        # Additional optimization: Track loss frequency and adjust risk parameters
        if len(recent_losses) >= 5:
            # If 5 or more losses in 24 hours, reduce position size by 20%
            self._adjust_position_size(-0.2)
        elif len(recent_losses) >= 3:
            # If 3 or more losses in 24 hours, reduce position size by 10%
            self._adjust_position_size(-0.1)
    
    def reset_daily_loss(self): 
        # Stub implementation 
        pass 

class Notifier: 
    def __init__(self): 
        pass 
    
    def send_alert(self, message): 
        # Stub implementation 
        logging.info(f"ALERT: {message}") 

logger = logging.getLogger(__name__) 

class RiskLevel(Enum): 
    LOW = "low" 
    MEDIUM = "medium" 
    HIGH = "high" 
    CRITICAL = "critical" 

@dataclass 
class Position: 
    token_address: str 
    amount: Decimal 
    entry_price: Decimal 
    current_price: Decimal 
    stop_loss_price: Decimal 
    take_profit_price: Decimal 
    trailing_stop_price: Decimal 
    risk_level: RiskLevel 
    timestamp: float 

@dataclass 
class RiskMetrics: 
    total_exposure: Decimal 
    max_position_size: Decimal 
    daily_loss_limit: Decimal 
    current_daily_loss: Decimal 
    volatility_threshold: Decimal 
    max_slippage: Decimal 

class RiskManager: 
    def __init__(self, config: Config, wallet: Wallet, db: Database, notifier: Notifier): 
        self.config = config 
        self.wallet = wallet 
        self.db = db 
        self.notifier = notifier 
        self.client = Client(config.SOLANA_RPC_URL) 
        
        # Risk parameters 
        self.max_position_size_percent = Decimal('0.1')  # 10% of portfolio 
        self.max_daily_loss_percent = Decimal('0.05')    # 5% of portfolio 
        self.stop_loss_percent = Decimal('0.15')         # 15% SL 
        self.take_profit_percent = Decimal('0.30')       # 30% TP 
        self.trailing_stop_buffer = Decimal('0.02')      # 2% trailing stop buffer 
        self.max_volatility = Decimal('0.5')             # 50% volatility threshold 
        self.max_slippage_allowed = Decimal('0.02')      # 2% slippage 
        self.cooldown_period = 300  # 5 minutes cooldown after stop loss 
        
        # Tracking 
        self.positions: Dict[str, Position] = {} 
        self.last_stop_loss_time: Dict[str, float] = {} 
        self.daily_losses: Decimal = Decimal('0') 
        self.last_reset_time = time.time() 
        
        # Initialize from database 
        self._load_positions_from_db() 
        
    def _load_positions_from_db(self): 
        """Load existing positions from database""" 
        try: 
            positions_data = self.db.get_active_positions() 
            for pos_data in positions_data: 
                position = Position( 
                    token_address=pos_data['token_address'], 
                    amount=Decimal(str(pos_data['amount'])), 
                    entry_price=Decimal(str(pos_data['entry_price'])), 
                    current_price=Decimal(str(pos_data['current_price'])), 
                    stop_loss_price=Decimal(str(pos_data['stop_loss_price'])), 
                    take_profit_price=Decimal(str(pos_data['take_profit_price'])), 
                    trailing_stop_price=Decimal(str(pos_data.get('trailing_stop_price', pos_data['stop_loss_price']))), 
                    risk_level=RiskLevel(pos_data['risk_level']), 
                    timestamp=pos_data['timestamp'] 
                ) 
                self.positions[pos_data['token_address']] = position 
            logger.info(f"Loaded {len(self.positions)} positions from database") 
        except Exception as e: 
            logger.error(f"Error loading positions from database: {e}") 
            
    def calculate_position_size(self, token_price: Decimal, volatility: Decimal) -> Decimal:
        """Calculate appropriate position size based on risk parameters"""
        try:
            # Get available SOL balance
            sol_balance = self.wallet.get_balance()

            # Enhanced volatility-based position sizing with optimized risk parameters
            if volatility > self.max_volatility * Decimal('0.85'):
                volatility_factor = Decimal('0.3')  # Very high volatility - minimal positions
            elif volatility > self.max_volatility * Decimal('0.65'):
                volatility_factor = Decimal('0.55')   # High volatility - small positions
            elif volatility > self.max_volatility * Decimal('0.35'):
                volatility_factor = Decimal('0.8')  # Medium volatility - balanced positions
            else:
                volatility_factor = Decimal('1.0')   # Low volatility - full positions

            # Risk-aware position sizing with optimized diversification
            active_positions = len(self.positions)
            position_diversification_factor = max(Decimal('0.15'), Decimal('1.0') - Decimal(str(active_positions)) * Decimal('0.12'))

            # Account for existing positions in wallet with improved exposure management
            total_exposure = sum(pos.size * pos.entry_price for pos in self.positions.values())
            exposure_factor = max(Decimal('0.15'), (sol_balance * Decimal('1.8') - total_exposure) / (sol_balance * Decimal('1.8')))

            # Calculate max position size with enhanced risk adjustment
            risk_adjustment = min(Decimal('1.2'), sol_balance / Decimal('4'))  # More aggressive but controlled scaling
            max_position_value = sol_balance * self.max_position_size_percent * volatility_factor * risk_adjustment * position_diversification_factor * exposure_factor

            # Convert to token amount with minimum size check
            position_size = max_position_value / token_price

            # Ensure minimum position size for low price tokens
            min_position_value = Decimal('0.075')  # Optimized minimum position value
            if max_position_value < min_position_value:
                position_size = min_position_value / token_price

            logger.info(f"Calculated position size: {position_size} tokens at price {token_price} with volatility factor {volatility_factor}")
            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return Decimal('0')
            
    def check_stop_loss(self, token_address: str, current_price: Decimal) -> bool: 
        """Check if stop loss should be triggered""" 
        if token_address not in self.positions: 
            return False 
            
        position = self.positions[token_address] 
        position.current_price = current_price 
        
        # Update trailing stop if price increased by more than buffer
        self._update_trailing_stop(position, current_price)
        
        # Update in database 
        self._update_position_in_db(position) 
        
        if current_price <= position.stop_loss_price or current_price <= position.trailing_stop_price: 
            reason = "STOP LOSS" if current_price <= position.stop_loss_price else "TRAILING STOP"
            logger.info(f"{reason} triggered for {token_address} at price {current_price}") 
            self.notifier.send_alert(f"{reason}: Sold {token_address} at {current_price}") 
            return True 
            
        return False 
        
    def check_take_profit(self, token_address: str, current_price: Decimal) -> bool: 
        """Check if take profit should be triggered""" 
        if token_address not in self.positions: 
            return False 

        position = self.positions[token_address] 
        position.current_price = current_price 

        # Update trailing stop if price increased by more than buffer
        self._update_trailing_stop(position, current_price)

        # Update in database 
        self._update_position_in_db(position) 

        # Enhanced take profit logic with multiple profit levels
        # Primary take profit level
        take_profit_threshold = position.take_profit_price * Decimal('0.995')  # 0.5% buffer

        # Early profit taking for high momentum moves (2% gain)
        early_take_profit = position.entry_price * Decimal('1.02')

        # Check for early take profit opportunity first
        if current_price >= early_take_profit and position.pnl_percentage >= Decimal('1.5'):
            logger.info(f"Early take profit triggered for {token_address} at price {current_price}")
            self.notifier.send_alert(f"EARLY TAKE PROFIT: Sold {token_address} at {current_price}")
            return True

        # Check primary take profit with dynamic threshold based on market volatility
        if current_price >= take_profit_threshold: 
            logger.info(f"Take profit triggered for {token_address} at price {current_price}") 
            self.notifier.send_alert(f"TAKE PROFIT: Sold {token_address} at {current_price}") 
            return True 

        return False
        
    def _update_trailing_stop(self, position: Position, current_price: Decimal):
        """Update trailing stop price based on current price and buffer with multi-tier exit strategy"""
        # Calculate trailing stop price (2% below current price)
        trailing_stop_candidate = current_price * (1 - self.trailing_stop_buffer)

        # Only update if the new trailing stop is higher than existing one
        if trailing_stop_candidate > position.trailing_stop_price:
            position.trailing_stop_price = trailing_stop_candidate
            logger.info(f"Updated trailing stop for {position.token_address} to {position.trailing_stop_price}")

        # Multi-tier exit strategy based on profit levels
        if position.entry_price > 0:
            price_change_pct = (current_price - position.entry_price) / position.entry_price

            # Tier 1: 5% profit - tighten trailing stop to 1% below current price
            if price_change_pct > Decimal('0.05') and price_change_pct <= Decimal('0.10'):
                optimized_trailing_stop = current_price * (1 - Decimal('0.01'))
                if optimized_trailing_stop > position.trailing_stop_price:
                    position.trailing_stop_price = optimized_trailing_stop
                    logger.info(f"Tier 1 trailing stop for {position.token_address} to {position.trailing_stop_price} ({price_change_pct*100:.2f}% profit)")

            # Tier 2: 10% profit - tighten trailing stop to 0.5% below current price
            elif price_change_pct > Decimal('0.10') and price_change_pct <= Decimal('0.20'):
                optimized_trailing_stop = current_price * (1 - Decimal('0.005'))
                if optimized_trailing_stop > position.trailing_stop_price:
                    position.trailing_stop_price = optimized_trailing_stop
                    logger.info(f"Tier 2 trailing stop for {position.token_address} to {position.trailing_stop_price} ({price_change_pct*100:.2f}% profit)")

            # Tier 3: 20%+ profit - tighten trailing stop to 0.25% below current price
            elif price_change_pct > Decimal('0.20'):
                optimized_trailing_stop = current_price * (1 - Decimal('0.0025'))
                if optimized_trailing_stop > position.trailing_stop_price:
                    position.trailing_stop_price = optimized_trailing_stop
                    logger.info(f"Tier 3 trailing stop for {position.token_address} to {position.trailing_stop_price} ({price_change_pct*100:.2f}% profit)")
        
    def add_position(self, token_address: str, amount: Decimal, entry_price: Decimal, 
                     stop_loss_price: Decimal, take_profit_price: Decimal) -> bool: 
        """Add a new position with risk management""" 
        try: 
            # Check if we're in cooldown period after stop loss 
            if self._is_in_cooldown(token_address): 
                logger.warning(f"Token {token_address} is in cooldown period") 
                return False 
                
            # Check daily loss limit 
            if self._check_daily_loss_limit(): 
                logger.warning("Daily loss limit reached") 
                self.notifier.send_alert("DAILY LOSS LIMIT REACHED - No new positions") 
                return False 
                
            # Check total exposure 
            if self._check_total_exposure(amount * entry_price): 
                logger.warning("Total exposure limit reached") 
                self.notifier.send_alert("EXPOSURE LIMIT REACHED - No new positions") 
                return False 
                
            # Create position with trailing stop initialized to stop loss price
            position = Position( 
                token_address=token_address, 
                amount=amount, 
                entry_price=entry_price, 
                current_price=entry_price, 
                stop_loss_price=stop_loss_price, 
                take_profit_price=take_profit_price, 
                trailing_stop_price=stop_loss_price,  # Initialize trailing stop to stop loss price
                risk_level=self._assess_risk_level(entry_price, stop_loss_price, take_profit_price), 
                timestamp=time.time() 
            ) 
            
            self.positions[token_address] = position 
            self._save_position_to_db(position) 
            
            logger.info(f"Added new position: {token_address} - {amount} tokens at {entry_price}") 
            self.notifier.send_alert(f"NEW POSITION: Bought {amount} {token_address} at {entry_price}") 
            
            return True 
            
        except Exception as e: 
            logger.error(f"Error adding position: {e}") 
            return False 
            
    def remove_position(self, token_address: str, exit_price: Decimal, is_stop_loss: bool = False): 
        """Remove a position and update risk metrics""" 
        try: 
            if token_address not in self.positions: 
                return 
                
            position = self.positions[token_address] 
            
            # Calculate PnL 
            pnl = (exit_price - position.entry_price) * position.amount 
            
            # Update daily losses if it's a loss 
            if pnl < 0: 
                self.daily_losses += abs(pnl) 
                self._save_daily_loss_to_db(abs(pnl)) 
                
                # Update stop loss time if applicable 
                if is_stop_loss: 
                    self.last_stop_loss_time[token_address] = time.time() 
            
            # Remove position 
            del self.positions[token_address] 
            self._remove_position_from_db(token_address) 
            
            logger.info(f"Removed position: {token_address} at price {exit_price}, PnL: {pnl}") 
            if is_stop_loss: 
                self.notifier.send_alert(f"STOP LOSS: Sold {token_address} at {exit_price}, Loss: {abs(pnl)}") 
            
        except Exception as e: 
            logger.error(f"Error removing position: {e}") 
            
    def _assess_risk_level(self, entry_price: Decimal, stop_loss_price: Decimal, 
                          take_profit_price: Decimal) -> RiskLevel: 
        """Assess the risk level of a position""" 
        try: 
            stop_loss_distance = (entry_price - stop_loss_price) / entry_price 
            take_profit_distance = (take_profit_price - entry_price) / entry_price 
            
            # Risk-reward ratio 
            if take_profit_distance == 0: 
                return RiskLevel.CRITICAL 
                
            risk_reward_ratio = stop_loss_distance / take_profit_distance 
            
            if risk_reward_ratio > Decimal('0.5'): 
                return RiskLevel.HIGH 
            elif risk_reward_ratio > Decimal('0.3'): 
                return RiskLevel.MEDIUM 
            else: 
                return RiskLevel.LOW 
                
        except Exception as e: 
            logger.error(f"Error assessing risk level: {e}") 
            return RiskLevel.HIGH 
            
    def _check_daily_loss_limit(self) -> bool: 
        """Check if daily loss limit has been reached""" 
        # Reset daily losses if it's a new day 
        if time.time() - self.last_reset_time > 86400:  # 24 hours 
            self.daily_losses = Decimal('0') 
            self.last_reset_time = time.time() 
            self._reset_daily_loss_in_db() 
            
        sol_balance = self.wallet.get_balance() 
        daily_loss_limit = sol_balance * self.max_daily_loss_percent 
        
        return self.daily_losses >= daily_loss_limit 
        
    def _check_total_exposure(self, new_position_value: Decimal) -> bool: 
        """Check if total exposure exceeds limit""" 
        total_exposure = new_position_value 
        for position in self.positions.values(): 
            total_exposure += position.amount * position.current_price 
            
        sol_balance = self.wallet.get_balance() 
        max_exposure = sol_balance * Decimal('0.5')  # Max 50% exposure 
        
        return total_exposure >= max_exposure 
        
    def _is_in_cooldown(self, token_address: str) -> bool: 
        """Check if token is in cooldown period after stop loss""" 
        if token_address not in self.last_stop_loss_time: 
            return False 
            
        return time.time() - self.last_stop_loss_time[token_address] < self.cooldown_period 
        
    def get_risk_metrics(self) -> RiskMetrics: 
        """Get current risk metrics""" 
        try: 
            sol_balance = self.wallet.get_balance() 
            
            total_exposure = Decimal('0') 
            for position in self.positions.values(): 
                total_exposure += position.amount * position.current_price 
                
            return RiskMetrics( 
                total_exposure=total_exposure, 
                max_position_size=sol_balance * self.max_position_size_percent, 
                daily_loss_limit=sol_balance * self.max_daily_loss_percent, 
                current_daily_loss=self.daily_losses, 
                volatility_threshold=self.max_volatility, 
                max_slippage=self.max_slippage_allowed 
            ) 
            
        except Exception as e: 
            logger.error(f"Error getting risk metrics: {e}") 
            return RiskMetrics( 
                total_exposure=Decimal('0'), 
                max_position_size=Decimal('0'), 
                daily_loss_limit=Decimal('0'), 
                current_daily_loss=Decimal('0'), 
                volatility_threshold=Decimal('0'), 
                max_slippage=Decimal('0') 
            ) 
            
    def update_position_prices(self, price_updates: Dict[str, Decimal]): 
        """Update current prices for all positions""" 
        try: 
            for token_address, current_price in price_updates.items(): 
                if token_address in self.positions: 
                    self.positions[token_address].current_price = current_price 
                    # Update trailing stop if price increased by more than buffer
                    self._update_trailing_stop(self.positions[token_address], current_price)
                    self._update_position_in_db(self.positions[token_address]) 
                    
        except Exception as e: 
            logger.error(f"Error updating position prices: {e}") 
            
    def _save_position_to_db(self, position: Position): 
        """Save position to database""" 
        try: 
            position_data = { 
                'token_address': position.token_address, 
                'amount': str(position.amount), 
                'entry_price': str(position.entry_price), 
                'current_price': str(position.current_price), 
                'stop_loss_price': str(position.stop_loss_price), 
                'take_profit_price': str(position.take_profit_price), 
                'trailing_stop_price': str(position.trailing_stop_price), 
                'risk_level': position.risk_level.value, 
                'timestamp': position.timestamp 
            } 
            self.db.save_position(position_data) 
        except Exception as e: 
            logger.error(f"Error saving position to database: {e}") 
            
    def _update_position_in_db(self, position: Position): 
        """Update position in database""" 
        try: 
            position_data = { 
                'token_address': position.token_address, 
                'current_price': str(position.current_price), 
                'trailing_stop_price': str(position.trailing_stop_price) 
            } 
            self.db.update_position(position_data) 
        except Exception as e: 
            logger.error(f"Error updating position in database: {e}") 
            
    def _remove_position_from_db(self, token_address: str): 
        """Remove position from database""" 
        try: 
            self.db.remove_position(token_address) 
        except Exception as e: 
            logger.error(f"Error removing position from database: {e}") 
            
    def _save_daily_loss_to_db(self, loss_amount: Decimal): 
        """Save daily loss to database""" 
        try: 
            self.db.save_daily_loss(str(loss_amount), time.time()) 
        except Exception as e: 
            logger.error(f"Error saving daily loss to database: {e}") 
            
    def _reset_daily_loss_in_db(self): 
        """Reset daily loss in database""" 
        try: 
            self.db.reset_daily_loss() 
        except Exception as e: 
            logger.error(f"Error resetting daily loss in database: {e}") 
            
    def get_positions_summary(self) -> Dict[str, Any]: 
        """Get summary of all positions""" 
        try: 
            summary = { 
                'total_positions': len(self.positions), 
                'positions': [] 
            } 
            
            for token_address, position in self.positions.items(): 
                pnl = (position.current_price - position.entry_price) * position.amount 
                pnl_percent = ((position.current_price / position.entry_price) - 1) * 100 
                
                position_summary = { 
                    'token': token_address, 
                    'amount': str(position.amount), 
                    'entry_price': str(position.entry_price), 
                    'current_price': str(position.current_price), 
                    'pnl': str(pnl), 
                    'pnl_percent': str(pnl_percent), 
                    'stop_loss_price': str(position.stop_loss_price), 
                    'take_profit_price': str(position.take_profit_price), 
                    'trailing_stop_price': str(position.trailing_stop_price), 
                    'risk_level': position.risk_level.value 
                } 
                summary['positions'].append(position_summary) 
                
            return summary 
            
        except Exception as e: 
            logger.error(f"Error getting positions summary: {e}") 
            return {'total_positions': 0, 'positions': []}