import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

# ANSI color codes for console output
class Colors:
    """ANSI color codes for console logging"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages"""
    
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BG_RED + Colors.WHITE,
    }
    
    def format(self, record):
        # Create a copy of the record to avoid modifying the original
        record_copy = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            func=record.funcName
        )
        
        # Copy all attributes
        for attr in dir(record):
            if not attr.startswith('_'):
                try:
                    setattr(record_copy, attr, getattr(record, attr))
                except (AttributeError, TypeError):
                    pass
        
        # Add color to the level name
        if hasattr(record_copy, 'levelname'):
            color = self.COLORS.get(record_copy.levelname, Colors.RESET)
            record_copy.levelname = f"{color}{record_copy.levelname}{Colors.RESET}"
        
        # Add color to the module name
        if hasattr(record_copy, 'module'):
            record_copy.module = f"{Colors.BLUE}{record_copy.module}{Colors.RESET}"
        
        return super().format(record_copy)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present (using getattr to avoid linter issues)
        extra_fields = getattr(record, 'extra_fields', None)
        if extra_fields:
            log_entry.update(extra_fields)
        
        return json.dumps(log_entry)

class AppLogger:
    """Main logging class that handles all logging configuration and provides simple interface"""
    
    def __init__(self, app_name: str = "smart-dashboard", log_dir: str = "website/logs"):
        self.app_name = app_name
        # Always resolve log_dir relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        self.log_dir = (project_root / log_dir).resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all logging handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs (plain text, no colors)
        all_logs_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        all_logs_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        all_logs_handler.setFormatter(file_formatter)
        self.logger.addHandler(all_logs_handler)
        
        # Error log file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # JSON log file for structured logging
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_structured.json",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
    
    def _log_with_context(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal method to log with extra context"""
        if extra_fields:
            # Add extra fields to kwargs
            kwargs['extra'] = {'extra_fields': extra_fields}
        self.logger.log(level, message, **kwargs)
    
    # Simple logging methods
    def debug(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, extra_fields, **kwargs)
    
    def info(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, extra_fields, **kwargs)
    
    def warning(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, extra_fields, **kwargs)
    
    def error(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        self._log_with_context(logging.ERROR, message, extra_fields, **kwargs)
    
    def critical(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, extra_fields, **kwargs)
    
    def exception(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs):
        """Log exception with traceback"""
        self._log_with_context(logging.ERROR, message, extra_fields, exc_info=True, **kwargs)
    
    # Specialized logging methods
    def request(self, method: str, url: str, status_code: int, duration: float, user_id: Optional[str] = None):
        """Log HTTP request details"""
        extra_fields = {
            'type': 'http_request',
            'method': method,
            'url': url,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'user_id': user_id
        }
        level = logging.INFO if status_code < 400 else logging.WARNING
        self._log_with_context(level, f"{method} {url} - {status_code} ({duration:.3f}s)", extra_fields)
    
    def database(self, operation: str, collection: str, duration: float, success: bool, error: Optional[str] = None):
        """Log database operations"""
        extra_fields = {
            'type': 'database',
            'operation': operation,
            'collection': collection,
            'duration_ms': round(duration * 1000, 2),
            'success': success
        }
        if error:
            extra_fields['error'] = error
        
        level = logging.INFO if success else logging.ERROR
        message = f"DB {operation} on {collection} - {'SUCCESS' if success else 'FAILED'}"
        if error:
            message += f" - {error}"
        self._log_with_context(level, message, extra_fields)
    
    def auth(self, action: str, user_id: Optional[str] = None, success: bool = True, ip: Optional[str] = None):
        """Log authentication events"""
        extra_fields = {
            'type': 'authentication',
            'action': action,
            'user_id': user_id,
            'success': success,
            'ip_address': ip
        }
        level = logging.INFO if success else logging.WARNING
        message = f"Auth {action} - {'SUCCESS' if success else 'FAILED'}"
        if user_id:
            message += f" (user: {user_id})"
        self._log_with_context(level, message, extra_fields)
    
    def file_upload(self, filename: str, file_size: int, user_id: str, success: bool, error: Optional[str] = None):
        """Log file upload events"""
        extra_fields = {
            'type': 'file_upload',
            'filename': filename,
            'file_size_bytes': file_size,
            'user_id': user_id,
            'success': success
        }
        if error:
            extra_fields['error'] = error
        
        level = logging.INFO if success else logging.ERROR
        message = f"File upload {filename} ({file_size} bytes) - {'SUCCESS' if success else 'FAILED'}"
        if error:
            message += f" - {error}"
        self._log_with_context(level, message, extra_fields)

# Global logger instance
_logger_instance = None

def get_logger(app_name: str = "smart-dashboard", log_dir: str = "website/logs") -> AppLogger:
    """Get or create the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger(app_name, log_dir)
    return _logger_instance

# Export the logger instance for direct usage
logger = get_logger() 