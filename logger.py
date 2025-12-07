import logging
import sys
import os
from datetime import datetime
from typing import Optional

class Logger:
    """Advanced Logging System v15.0.00"""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create log formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Get current date for log file naming
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create file handlers
        # Main log file
        main_handler = logging.FileHandler(
            f'{self.log_dir}/bot_{current_date}.log',
            encoding='utf-8'
        )
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(self.log_level)
        
        # Error log file
        error_handler = logging.FileHandler(
            f'{self.log_dir}/error_{current_date}.log',
            encoding='utf-8'
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(self.log_level)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplication
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        root_logger.propagate = False
        
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance with specified name"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_command(user_id: int, command: str, success: bool = True, details: dict = None):
        """Log user commands"""
        logger = logging.getLogger('command_logger')
        details = details or {}
        
        log_message = f"CMD: {command} | User: {user_id} | Success: {success}"
        if details:
            log_message += f" | Details: {details}"
        
        if success:
            logger.info(log_message)
        else:
            logger.warning(log_message)
    
    @staticmethod
    def log_error(error_type: str, error_message: str, user_id: Optional[int] = None, traceback: str = None):
        """Log errors with context"""
        logger = logging.getLogger('error_logger')
        
        log_message = f"ERROR: {error_type} | Message: {error_message}"
        if user_id:
            log_message += f" | User: {user_id}"
        
        logger.error(log_message)
        if traceback:
            logger.debug(f"Traceback: {traceback}")
    
    @staticmethod
    def log_payment(transaction_id: str, amount: float, user_id: int, status: str, method: str = None):
        """Log payment transactions"""
        logger = logging.getLogger('payment_logger')
        
        log_message = f"PAYMENT: {transaction_id} | Amount: {amount} | User: {user_id} | Status: {status}"
        if method:
            log_message += f" | Method: {method}"
        
        logger.info(log_message)
    
    @staticmethod
    def log_game(game_type: str, user_id: int, bet: float, result: str, profit: float):
        """Log game activities"""
        logger = logging.getLogger('game_logger')
        
        log_message = f"GAME: {game_type} | User: {user_id} | Bet: {bet} | Result: {result} | Profit: {profit}"
        logger.info(log_message)
    
    @staticmethod
    def log_admin_action(admin_id: int, action: str, target_id: int = None, details: dict = None):
        """Log admin actions"""
        logger = logging.getLogger('admin_logger')
        
        log_message = f"ADMIN: {admin_id} | Action: {action}"
        if target_id:
            log_message += f" | Target: {target_id}"
        if details:
            log_message += f" | Details: {details}"
        
        logger.info(log_message)
    
    @staticmethod
    def get_log_files() -> list:
        """Get list of log files"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                file_path = os.path.join(log_dir, file)
                stats = os.stat(file_path)
                log_files.append({
                    'name': file,
                    'size': stats.st_size,
                    'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 30):
        """Cleanup old log files"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                file_path = os.path.join(log_dir, file)
                stats = os.stat(file_path)
                
                if stats.st_mtime < cutoff_date:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logging.info(f"Deleted old log file: {file}")
                    except Exception as e:
                        logging.error(f"Failed to delete log file {file}: {e}")
        
        return deleted_count
    
    @staticmethod
    def log_system_info():
        """Log system information"""
        logger = logging.getLogger('system_logger')
        
        import psutil
        import platform
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # System info
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version(),
                'cpu_cores': psutil.cpu_count(),
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory_percent,
                'memory_used_gb': round(memory_used_gb, 2),
                'memory_total_gb': round(memory_total_gb, 2),
                'disk_usage_percent': disk_percent,
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_total_gb': round(disk_total_gb, 2),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            logger.info(f"SYSTEM INFO: {system_info}")
            return system_info
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return None
    
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors for console output"""
        
        COLORS = {
            'DEBUG': '\033[94m',    # Blue
            'INFO': '\033[92m',     # Green
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',    # Red
            'CRITICAL': '\033[95m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        def format(self, record):
            # Add color based on log level
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            message = super().format(record)
            return f"{color}{message}{self.COLORS['RESET']}"