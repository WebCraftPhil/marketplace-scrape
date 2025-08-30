"""
Configuration management for Etsy Market Research Scraper
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the Etsy scraper"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file and environment variables"""
        # Load environment variables
        load_dotenv()
        
        # Load YAML config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_yaml_config()
        self._env_config = self._load_env_config()
        
        # Merge configurations (env vars override YAML)
        self._merged_config = self._merge_configs()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        # Scraping settings
        env_config['scraping'] = {
            'min_delay': int(os.getenv('SCRAPING_MIN_DELAY', 2)),
            'max_delay': int(os.getenv('SCRAPING_MAX_DELAY', 8)),
            'max_retries': int(os.getenv('SCRAPING_MAX_RETRIES', 3)),
            'timeout': int(os.getenv('SCRAPING_TIMEOUT', 15000)),
            'headless': os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
        }
        
        # Features
        env_config['features'] = {
            'enable_google_trends': True,  # Default enabled
            'enable_etsy_analysis': True,  # Default enabled
            'enable_amazon_analysis': False,  # Default disabled
            'enable_social_analysis': False  # Default disabled
        }
        
        # Output settings
        env_config['output'] = {
            'csv_filename': os.getenv('OUTPUT_CSV_FILENAME', 'etsy_market_research.csv'),
            'summary_filename': os.getenv('OUTPUT_SUMMARY_FILENAME', 'opportunity_summary.txt'),
            'log_filename': os.getenv('OUTPUT_LOG_FILENAME', 'scraping_log.txt'),
            'checkpoint_filename': os.getenv('OUTPUT_CHECKPOINT_FILENAME', 'scraping_checkpoint.json')
        }
        
        # Competition thresholds
        env_config['competition'] = {
            'low_threshold': int(os.getenv('COMPETITION_LOW_THRESHOLD', 1000)),
            'moderate_threshold': int(os.getenv('COMPETITION_MODERATE_THRESHOLD', 10000)),
            'high_threshold': int(os.getenv('COMPETITION_HIGH_THRESHOLD', 100000))
        }
        
        # Logging
        env_config['logging'] = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': os.getenv('LOG_FORMAT', 'json'),
            'file_rotation': os.getenv('LOG_FILE_ROTATION', 'daily'),
            'max_file_size': os.getenv('LOG_MAX_FILE_SIZE', '10MB'),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 7))
        }
        
        # Development
        env_config['development'] = {
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            'save_screenshots': os.getenv('SAVE_SCREENSHOTS', 'true').lower() == 'true',
            'verbose_logging': os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
        }
        
        return env_config
    
    def _merge_configs(self) -> Dict[str, Any]:
        """Merge YAML and environment configurations"""
        merged = self._config.copy()
        
        # Deep merge environment config (env vars take precedence)
        for section, values in self._env_config.items():
            if section not in merged:
                merged[section] = {}
            merged[section].update(values)
        
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'scraping.min_delay')"""
        keys = key.split('.')
        value = self._merged_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration"""
        return self._merged_config.get('scraping', {})
    
    def get_features_config(self) -> Dict[str, Any]:
        """Get features configuration"""
        return self._merged_config.get('features', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self._merged_config.get('output', {})
    
    def get_competition_config(self) -> Dict[str, Any]:
        """Get competition analysis configuration"""
        return self._merged_config.get('competition', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._merged_config.get('logging', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """Get development configuration"""
        return self._merged_config.get('development', {})
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('development.debug_mode', False)
    
    def should_save_screenshots(self) -> bool:
        """Check if screenshots should be saved"""
        return self.get('development.save_screenshots', True)


# Global configuration instance
config = Config()
