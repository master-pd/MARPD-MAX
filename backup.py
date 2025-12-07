import os
import shutil
import json
import zipfile
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pickle
from config import Config
from logger import Logger

class BackupManager:
    """Advanced Backup Management System v15.0.00"""
    
    def __init__(self, db):
        self.db = db
        self.config = Config()
        self.logger = Logger.get_logger(__name__)
        
        # Backup configuration
        self.backup_config = {
            'auto_backup': True,
            'backup_interval_hours': 24,
            'max_backups': 30,
            'backup_dir': 'backups',
            'backup_time': '03:00',  # Daily at 3 AM
            'compress_backups': True,
            'backup_types': ['database', 'logs', 'config'],
            'notification_on_backup': True
        }
        
        # Create backup directory
        os.makedirs(self.backup_config['backup_dir'], exist_ok=True)
        
        # Load backup history
        self.backup_history = self._load_backup_history()
        
        self.logger.info("🔧 Backup Manager v15.0.00 Initialized")
    
    def _load_backup_history(self) -> List[Dict]:
        """Load backup history from file"""
        history_file = os.path.join(self.backup_config['backup_dir'], 'backup_history.json')
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def _save_backup_history(self):
        """Save backup history to file"""
        history_file = os.path.join(self.backup_config['backup_dir'], 'backup_history.json')
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save backup history: {e}")
    
    def create_backup(self, backup_name: str = None, backup_type: str = 'full') -> Dict:
        """Create comprehensive backup"""
        try:
            start_time = datetime.now()
            
            if not backup_name:
                backup_name = f"backup_{start_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup directory
            backup_path = os.path.join(self.backup_config['backup_dir'], backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            backup_data = {
                'name': backup_name,
                'type': backup_type,
                'timestamp': start_time.isoformat(),
                'version': self.config.VERSION,
                'files': []
            }
            
            # Backup database
            if 'database' in self.backup_config['backup_types'] or backup_type == 'full':
                self._backup_database(backup_path, backup_data)
            
            # Backup logs
            if 'logs' in self.backup_config['backup_types'] or backup_type == 'full':
                self._backup_logs(backup_path, backup_data)
            
            # Backup configuration
            if 'config' in self.backup_config['backup_types'] or backup_type == 'full':
                self._backup_config(backup_path, backup_data)
            
            # Create manifest file
            manifest_file = os.path.join(backup_path, 'manifest.json')
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Compress backup if enabled
            final_backup_path = backup_path
            if self.backup_config['compress_backups']:
                final_backup_path = self._compress_backup(backup_path)
            
            # Calculate backup size
            backup_size = 0
            if os.path.exists(final_backup_path):
                if self.backup_config['compress_backups']:
                    backup_size = os.path.getsize(final_backup_path)
                else:
                    for root, dirs, files in os.walk(final_backup_path):
                        for file in files:
                            backup_size += os.path.getsize(os.path.join(root, file))
            
            # Create backup entry
            backup_entry = {
                'id': backup_name,
                'name': backup_name,
                'type': backup_type,
                'timestamp': start_time.isoformat(),
                'size': backup_size,
                'path': final_backup_path,
                'duration': (datetime.now() - start_time).total_seconds(),
                'status': 'COMPLETED',
                'files': len(backup_data['files'])
            }
            
            # Add to history
            self.backup_history.append(backup_entry)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            # Save backup history
            self._save_backup_history()
            
            # Log successful backup
            self.logger.info(f"✅ Backup created: {backup_name} ({backup_size:,} bytes, {backup_entry['duration']:.2f}s)")
            
            # Send notification if enabled
            if self.backup_config['notification_on_backup']:
                self._send_backup_notification(backup_entry)
            
            return {
                'success': True,
                'message': f"✅ ব্যাকআপ তৈরি হয়েছে: {backup_name}",
                'backup': backup_entry
            }
            
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            return {
                'success': False,
                'message': f"❌ ব্যাকআপ ব্যর্থ হয়েছে: {str(e)}"
            }
    
    def _backup_database(self, backup_path: str, backup_data: Dict):
        """Backup database files"""
        data_dir = self.db.data_dir
        
        if os.path.exists(data_dir):
            db_backup_dir = os.path.join(backup_path, 'database')
            os.makedirs(db_backup_dir, exist_ok=True)
            
            # Copy all database files
            for file in os.listdir(data_dir):
                if file.endswith(('.pkl', '.json')):
                    src_file = os.path.join(data_dir, file)
                    dst_file = os.path.join(db_backup_dir, file)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                        backup_data['files'].append(f'database/{file}')
                        
                        # Get file info
                        stats = os.stat(src_file)
                        self.logger.debug(f"Backed up: {file} ({stats.st_size:,} bytes)")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to backup {file}: {e}")
    
    def _backup_logs(self, backup_path: str, backup_data: Dict):
        """Backup log files"""
        log_dir = 'logs'
        
        if os.path.exists(log_dir):
            log_backup_dir = os.path.join(backup_path, 'logs')
            os.makedirs(log_backup_dir, exist_ok=True)
            
            # Copy log files from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(log_dir, file)
                    
                    # Check file modification time
                    stats = os.stat(file_path)
                    file_date = datetime.fromtimestamp(stats.st_mtime)
                    
                    if file_date > cutoff_date:
                        try:
                            dst_file = os.path.join(log_backup_dir, file)
                            shutil.copy2(file_path, dst_file)
                            backup_data['files'].append(f'logs/{file}')
                        except Exception as e:
                            self.logger.error(f"Failed to backup log {file}: {e}")
    
    def _backup_config(self, backup_path: str, backup_data: Dict):
        """Backup configuration files"""
        config_files = ['.env', 'config.py', 'requirements.txt']
        
        config_backup_dir = os.path.join(backup_path, 'config')
        os.makedirs(config_backup_dir, exist_ok=True)
        
        for file in config_files:
            if os.path.exists(file):
                try:
                    dst_file = os.path.join(config_backup_dir, file)
                    shutil.copy2(file, dst_file)
                    backup_data['files'].append(f'config/{file}')
                except Exception as e:
                    self.logger.error(f"Failed to backup config {file}: {e}")
    
    def _compress_backup(self, backup_path: str) -> str:
        """Compress backup directory to zip file"""
        try:
            zip_file = f"{backup_path}.zip"
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            self.logger.debug(f"Compressed backup: {zip_file}")
            return zip_file
            
        except Exception as e:
            self.logger.error(f"Failed to compress backup: {e}")
            return backup_path
    
    def _cleanup_old_backups(self):
        """Cleanup old backups based on retention policy"""
        max_backups = self.backup_config['max_backups']
        
        if len(self.backup_history) <= max_backups:
            return
        
        # Sort backups by timestamp (oldest first)
        self.backup_history.sort(key=lambda x: x.get('timestamp', ''))
        
        # Remove oldest backups
        while len(self.backup_history) > max_backups:
            old_backup = self.backup_history.pop(0)
            
            # Delete backup file
            if os.path.exists(old_backup['path']):
                try:
                    if old_backup['path'].endswith('.zip'):
                        os.remove(old_backup['path'])
                    else:
                        shutil.rmtree(old_backup['path'])
                    
                    self.logger.info(f"🗑️ Deleted old backup: {old_backup['name']}")
                except Exception as e:
                    self.logger.error(f"Failed to delete old backup {old_backup['name']}: {e}")
        
        # Save updated history
        self._save_backup_history()
    
    def restore_backup(self, backup_id: str, restore_type: str = 'full') -> Dict:
        """Restore from backup"""
        try:
            # Find backup
            backup_entry = None
            for backup in self.backup_history:
                if backup['id'] == backup_id:
                    backup_entry = backup
                    break
            
            if not backup_entry:
                return {
                    'success': False,
                    'message': f"ব্যাকআপ খুঁজে পাওয়া যায়নি: {backup_id}"
                }
            
            backup_path = backup_entry['path']
            
            # Extract if compressed
            if backup_path.endswith('.zip'):
                extract_dir = backup_path.replace('.zip', '')
                
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                backup_path = extract_dir
            
            # Restore based on type
            if restore_type == 'database' or restore_type == 'full':
                self._restore_database(backup_path)
            
            if restore_type == 'logs' or restore_type == 'full':
                self._restore_logs(backup_path)
            
            if restore_type == 'config' or restore_type == 'full':
                self._restore_config(backup_path)
            
            # Cleanup extracted directory if we extracted from zip
            if backup_entry['path'].endswith('.zip') and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            self.logger.info(f"✅ Backup restored: {backup_id}")
            
            return {
                'success': True,
                'message': f"✅ ব্যাকআপ রিস্টোর করা হয়েছে: {backup_id}",
                'backup': backup_entry
            }
            
        except Exception as e:
            self.logger.error(f"❌ Restore failed: {e}")
            return {
                'success': False,
                'message': f"❌ ব্যাকআপ রিস্টোর ব্যর্থ হয়েছে: {str(e)}"
            }
    
    def _restore_database(self, backup_path: str):
        """Restore database from backup"""
        db_backup_dir = os.path.join(backup_path, 'database')
        
        if os.path.exists(db_backup_dir):
            # Stop any active database operations
            # (In production, you might want to lock the database)
            
            # Restore each file
            for file in os.listdir(db_backup_dir):
                if file.endswith(('.pkl', '.json')):
                    src_file = os.path.join(db_backup_dir, file)
                    dst_file = os.path.join(self.db.data_dir, file)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                        self.logger.debug(f"Restored: {file}")
                    except Exception as e:
                        self.logger.error(f"Failed to restore {file}: {e}")
            
            # Reload database
            self.db.users = self.db._load_data("users")
            self.db.payments = self.db._load_data("payments")
            self.db.shop = self.db._load_data("shop", self.db._default_shop())
            self.db.games = self.db._load_data("games")
            self.db.transactions = self.db._load_data("transactions")
            self.db.logs = self.db._load_data("logs")
            self.db.stats = self.db._load_data("stats", self.db._default_stats())
    
    def _restore_logs(self, backup_path: str):
        """Restore logs from backup"""
        logs_backup_dir = os.path.join(backup_path, 'logs')
        
        if os.path.exists(logs_backup_dir):
            for file in os.listdir(logs_backup_dir):
                if file.endswith('.log'):
                    src_file = os.path.join(logs_backup_dir, file)
                    dst_file = os.path.join('logs', file)
                    
                    try:
                        # Append to existing logs instead of overwriting
                        if os.path.exists(dst_file):
                            with open(src_file, 'r', encoding='utf-8') as src:
                                with open(dst_file, 'a', encoding='utf-8') as dst:
                                    dst.write('\n' + src.read())
                        else:
                            shutil.copy2(src_file, dst_file)
                        
                        self.logger.debug(f"Restored log: {file}")
                    except Exception as e:
                        self.logger.error(f"Failed to restore log {file}: {e}")
    
    def _restore_config(self, backup_path: str):
        """Restore configuration from backup"""
        config_backup_dir = os.path.join(backup_path, 'config')
        
        if os.path.exists(config_backup_dir):
            for file in os.listdir(config_backup_dir):
                src_file = os.path.join(config_backup_dir, file)
                dst_file = file  # Restore to current directory
                
                try:
                    shutil.copy2(src_file, dst_file)
                    self.logger.debug(f"Restored config: {file}")
                except Exception as e:
                    self.logger.error(f"Failed to restore config {file}: {e}")
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        # Add from history
        for backup in self.backup_history:
            # Check if backup file still exists
            if os.path.exists(backup['path']):
                backups.append(backup)
        
        # Also check backup directory for any missing from history
        backup_files = []
        for file in os.listdir(self.backup_config['backup_dir']):
            if file.endswith('.zip') or os.path.isdir(os.path.join(self.backup_config['backup_dir'], file)):
                file_path = os.path.join(self.backup_config['backup_dir'], file)
                
                # Skip if already in history
                if not any(b['path'] == file_path for b in backups):
                    try:
                        stats = os.stat(file_path)
                        
                        backup_info = {
                            'id': file.replace('.zip', ''),
                            'name': file,
                            'timestamp': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            'size': stats.st_size,
                            'path': file_path,
                            'status': 'FOUND'
                        }
                        
                        backups.append(backup_info)
                    except:
                        pass
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return backups
    
    def get_backup_stats(self) -> Dict:
        """Get backup statistics"""
        backups = self.list_backups()
        
        total_size = sum(b.get('size', 0) for b in backups)
        total_count = len(backups)
        
        # Count by type
        types_count = {}
        for backup in backups:
            backup_type = backup.get('type', 'unknown')
            types_count[backup_type] = types_count.get(backup_type, 0) + 1
        
        # Last backup info
        last_backup = backups[0] if backups else None
        
        # Disk space info
        disk_info = {}
        try:
            backup_dir = self.backup_config['backup_dir']
            total, used, free = shutil.disk_usage(backup_dir)
            
            disk_info = {
                'total': total,
                'used': used,
                'free': free,
                'used_percent': (used / total) * 100
            }
        except:
            pass
        
        return {
            'total_backups': total_count,
            'total_size': total_size,
            'types_count': types_count,
            'last_backup': last_backup,
            'disk_info': disk_info,
            'config': self.backup_config
        }
    
    def setup_auto_backup(self):
        """Setup automatic backup scheduling"""
        if not self.backup_config['auto_backup']:
            return
        
        backup_time = self.backup_config['backup_time']
        
        try:
            schedule.every().day.at(backup_time).do(self._auto_backup_task)
            self.logger.info(f"⏰ Auto-backup scheduled at {backup_time}")
        except Exception as e:
            self.logger.error(f"Failed to schedule auto-backup: {e}")
    
    def _auto_backup_task(self):
        """Automatic backup task"""
        self.logger.info("🔄 Running automatic backup...")
        
        try:
            result = self.create_backup(
                backup_name=f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}",
                backup_type='full'
            )
            
            if result['success']:
                self.logger.info(f"✅ Auto-backup completed: {result['backup']['name']}")
            else:
                self.logger.error(f"❌ Auto-backup failed: {result['message']}")
        
        except Exception as e:
            self.logger.error(f"❌ Auto-backup error: {e}")
    
    def _send_backup_notification(self, backup_entry: Dict):
        """Send backup completion notification"""
        try:
            notification = f"""
✅ **ব্যাকআপ তৈরি হয়েছে!**

📁 **নাম:** {backup_entry['name']}
📊 **আকার:** {self._format_size(backup_entry['size'])}
⏰ **সময়:** {datetime.fromisoformat(backup_entry['timestamp']).strftime('%d/%m/%Y %H:%M')}
🔄 **ধরন:** {backup_entry.get('type', 'full')}
📈 **ফাইল:** {backup_entry['files']}টি
⏱️ **সময় লেগেছে:** {backup_entry['duration']:.2f} সেকেন্ড

💾 **মোট ব্যাকআপ:** {len(self.backup_history)}টি
"""
            
            # Log the notification
            self.logger.info(f"📢 Backup notification: {backup_entry['name']}")
            
            # Here you could send notification via:
            # - Telegram message to admin
            # - Email
            # - Discord webhook
            # etc.
            
        except Exception as e:
            self.logger.error(f"Failed to send backup notification: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def run_scheduler(self):
        """Run backup scheduler in background"""
        self.logger.info("🚀 Starting backup scheduler...")
        
        self.setup_auto_backup()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start backup scheduler in background thread"""
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("✅ Backup scheduler started")