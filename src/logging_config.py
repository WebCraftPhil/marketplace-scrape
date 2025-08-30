"""
Logging configuration for Etsy Market Research Scraper
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import structlog
from rich.logging import RichHandler
from rich.console import Console

from .config import config


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class StructuredLogger:
    """Structured logger with JSON and rich console output"""
    
    def __init__(self, name: str = "etsy_scraper"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with file and console handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler with rich formatting
        console_handler = RichHandler(
            console=Console(),
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # File handler with JSON formatting
        log_config = config.get_logging_config()
        log_filename = log_config.get('log_filename', 'scraping_log.txt')
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_filename)
        log_path.parent.mkdir(exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        
        # Debug file handler (if debug mode is enabled)
        if config.is_debug_mode():
            debug_handler = logging.handlers.RotatingFileHandler(
                f"debug_{log_filename}",
                maxBytes=10 * 1024 * 1024,
                backupCount=3
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(JSONFormatter())
            logger.addHandler(debug_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Log info message with extra fields"""
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields"""
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with extra fields"""
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields"""
        self._log_with_extra(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with extra fields"""
        self._log_with_extra(logging.CRITICAL, message, **kwargs)
    
    def _log_with_extra(self, level: int, message: str, **kwargs):
        """Log message with extra fields"""
        record = self.logger.makeRecord(
            self.name, level, "", 0, message, (), None
        )
        record.extra_fields = kwargs
        self.logger.handle(record)
    
    def log_scraping_event(self, event_type: str, seed: str = None, 
                          suggestion: str = None, **kwargs):
        """Log scraping-specific events"""
        extra_fields = {
            'event_type': event_type,
            'seed': seed,
            'suggestion': suggestion,
            **kwargs
        }
        self.info(f"Scraping event: {event_type}", **extra_fields)
    
    def log_error_with_screenshot(self, error: Exception, screenshot_path: str = None):
        """Log error with optional screenshot path"""
        extra_fields = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'screenshot_path': screenshot_path
        }
        self.error(f"Error occurred: {error}", **extra_fields)


# Global logger instance
logger = StructuredLogger()


def get_logger(name: str = None) -> StructuredLogger:
    """Get a logger instance"""
    if name:
        return StructuredLogger(name)
    return logger


def setup_logging():
    """Set up logging configuration"""
    # Configure structlog for additional structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return logger
