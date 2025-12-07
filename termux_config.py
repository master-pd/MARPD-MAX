"""
Termux-specific configuration for MARPd Bot
"""

import os
import sys
from pathlib import Path

class TermuxConfig:
    """Configuration optimized for Termux/Android"""
    
    @staticmethod
    def setup_termux_environment():
        """Setup Termux-specific environment"""
        
        # Check if running in Termux
        is_termux = os.path.exists('/data/data/com.termux/files/usr')
        
        if not is_termux:
            return False
        
        print("📱 Termux environment detected")
        
        # Set Termux-specific paths
        termux_home = Path('/data/data/com.termux/files/home')
        
        # Create directories in Termux home
        directories = [
            'MARPD/data',
            'MARPD/logs', 
            'MARPD/backups',
            'MARPD/cache',
            'MARPD/media'
        ]
        
        for directory in directories:
            dir_path = termux_home / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            os.chmod(dir_path, 0o755)
        
        # Set environment variables
        os.environ['TERMUX'] = '1'
        os.environ['ANDROID_DATA'] = '/data/data/com.termux/files/usr'
        
        # Disable some heavy features in Termux
        os.environ['MARPD_LIGHT_MODE'] = '1'
        os.environ['DISABLE_HEAVY_FEATURES'] = '1'
        
        # Optimize for mobile
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Memory optimization
        import resource
        try:
            # Set soft limit to 512MB, hard limit to 1GB
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 1024 * 1024 * 1024))
        except:
            pass
        
        return True
    
    @staticmethod
    def optimize_for_mobile():
        """Optimize settings for mobile devices"""
        
        optimizations = {
            'database': {
                'cache_size': 1000,  # Smaller cache for mobile
                'journal_mode': 'WAL',
                'synchronous': 'NORMAL'
            },
            'logging': {
                'level': 'INFO',  # Less verbose logging
                'file_size': '5MB',  # Smaller log files
                'backup_count': 3
            },
            'cache': {
                'max_size': '50MB',  # Smaller cache
                'ttl': 300  # 5 minutes
            },
            'media': {
                'max_size': '10MB',  # Smaller media files
                'auto_compress': True
            },
            'games': {
                'max_concurrent': 2,  # Fewer concurrent games
                'animation': 'minimal'  # Minimal animations
            }
        }
        
        return optimizations
    
    @staticmethod
    def get_termux_permissions():
        """Check and request Termux permissions"""
        
        permissions = {
            'storage': False,
            'camera': False,
            'microphone': False,
            'location': False,
            'sms': False,
            'contacts': False
        }
        
        try:
            # Check storage permission
            test_file = Path('/data/data/com.termux/files/home/test.txt')
            test_file.touch(exist_ok=True)
            test_file.unlink(missing_ok=True)
            permissions['storage'] = True
            
            # You can add more permission checks here
            # using termux-api if installed
            
        except:
            pass
        
        return permissions
    
    @staticmethod
    def mobile_optimized_requirements():
        """Lightweight alternative requirements for mobile"""
        
        mobile_packages = [
            # Core (必须)
            'python-telegram-bot>=20.0',
            'python-dotenv>=1.0',
            
            # Lightweight alternatives
            'ujson>=5.0',  # Instead of standard json
            'orjson>=3.0',  # Fast JSON
            'tinydb>=4.0',  # Instead of SQLite
            'aiofiles>=23.0',  # Async file operations
            
            # Minimal dependencies
            'schedule>=1.0',
            'pytz>=2023.0',
            'requests>=2.28',
            
            # Optional (can be disabled)
            # 'Pillow>=9.0',  # Image processing
            # 'psutil>=5.0',  # System monitoring
        ]
        
        return mobile_packages
