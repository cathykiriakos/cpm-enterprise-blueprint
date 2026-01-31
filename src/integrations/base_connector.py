"""
Base Connector Framework
========================

Provides a standardized interface for connecting to external data sources.
All source-specific connectors inherit from BaseConnector.

Features:
- Retry logic with exponential backoff
- Connection pooling
- Audit logging
- Error handling
- Metrics emission

Author: Catherine Kiriakos
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Iterator
import logging
import time
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConnectorConfig:
    """Configuration for a data connector."""
    name: str
    source_system: str
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: int = 300
    credentials: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractResult:
    """Result of a data extraction operation."""
    source_system: str
    table_name: str
    record_count: int
    extract_timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "source_system": self.source_system,
            "table_name": self.table_name,
            "record_count": self.record_count,
            "extract_timestamp": self.extract_timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.
    
    Subclasses must implement:
    - connect()
    - disconnect()
    - extract()
    - get_schema()
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.is_connected = False
        self._connection = None
        self._metrics = {
            "extracts_attempted": 0,
            "extracts_succeeded": 0,
            "extracts_failed": 0,
            "total_records_extracted": 0,
            "total_extraction_time_seconds": 0,
        }
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the data source."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to the data source."""
        pass
    
    @abstractmethod
    def extract(self, table: str, **kwargs) -> Iterator[Dict]:
        """Extract data from a table. Yields records as dictionaries."""
        pass
    
    @abstractmethod
    def get_schema(self, table: str) -> Dict[str, str]:
        """Get schema information for a table."""
        pass
    
    def extract_with_retry(self, table: str, **kwargs) -> ExtractResult:
        """Extract data with automatic retry on failure."""
        self._metrics["extracts_attempted"] += 1
        start_time = time.time()
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                if not self.is_connected:
                    self.connect()
                
                records = list(self.extract(table, **kwargs))
                
                elapsed = time.time() - start_time
                self._metrics["extracts_succeeded"] += 1
                self._metrics["total_records_extracted"] += len(records)
                self._metrics["total_extraction_time_seconds"] += elapsed
                
                logger.info(f"Extracted {len(records)} records from {table} in {elapsed:.2f}s")
                
                return ExtractResult(
                    source_system=self.config.source_system,
                    table_name=table,
                    record_count=len(records),
                    extract_timestamp=datetime.now(),
                    success=True,
                    metadata={"records": records, "elapsed_seconds": elapsed}
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay_seconds * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
        
        self._metrics["extracts_failed"] += 1
        
        return ExtractResult(
            source_system=self.config.source_system,
            table_name=table,
            record_count=0,
            extract_timestamp=datetime.now(),
            success=False,
            error_message=last_error
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connector metrics."""
        return self._metrics.copy()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class FileConnector(BaseConnector):
    """Connector for file-based data sources (CSV, JSON)."""
    
    def __init__(self, config: ConnectorConfig, base_path: str = "data"):
        super().__init__(config)
        self.base_path = Path(base_path)
    
    def connect(self) -> bool:
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path not found: {self.base_path}")
        self.is_connected = True
        logger.info(f"Connected to file source: {self.base_path}")
        return True
    
    def disconnect(self) -> bool:
        self.is_connected = False
        return True
    
    def extract(self, table: str, **kwargs) -> Iterator[Dict]:
        import csv
        
        # Try CSV first, then JSON
        csv_path = self.base_path / f"{table}.csv"
        json_path = self.base_path / f"{table}.json"
        
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row
        elif json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
                for record in data:
                    yield record
        else:
            raise FileNotFoundError(f"No data file found for table: {table}")
    
    def get_schema(self, table: str) -> Dict[str, str]:
        # Read first record to infer schema
        for record in self.extract(table):
            return {k: type(v).__name__ for k, v in record.items()}
        return {}


class APIConnector(BaseConnector):
    """Connector for REST API data sources."""
    
    def __init__(self, config: ConnectorConfig, base_url: str):
        super().__init__(config)
        self.base_url = base_url.rstrip('/')
        self._session = None
    
    def connect(self) -> bool:
        try:
            import requests
            self._session = requests.Session()
            
            # Set auth if provided
            if 'api_key' in self.config.credentials:
                self._session.headers['Authorization'] = f"Bearer {self.config.credentials['api_key']}"
            
            self.is_connected = True
            logger.info(f"Connected to API: {self.base_url}")
            return True
        except ImportError:
            raise ImportError("requests library required: pip install requests")
    
    def disconnect(self) -> bool:
        if self._session:
            self._session.close()
        self.is_connected = False
        return True
    
    def extract(self, table: str, **kwargs) -> Iterator[Dict]:
        endpoint = kwargs.get('endpoint', f"/{table}")
        url = f"{self.base_url}{endpoint}"
        
        params = kwargs.get('params', {})
        page = 1
        
        while True:
            params['page'] = page
            response = self._session.get(url, params=params, timeout=self.config.timeout_seconds)
            response.raise_for_status()
            
            data = response.json()
            records = data if isinstance(data, list) else data.get('data', data.get('results', []))
            
            if not records:
                break
            
            for record in records:
                yield record
            
            # Check for pagination
            if isinstance(data, dict) and not data.get('has_more', data.get('next')):
                break
            
            page += 1
    
    def get_schema(self, table: str) -> Dict[str, str]:
        for record in self.extract(table):
            return {k: type(v).__name__ for k, v in record.items()}
        return {}


class DatabaseConnector(BaseConnector):
    """Connector for SQL databases (PostgreSQL, MySQL, etc.)."""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._cursor = None
    
    def connect(self) -> bool:
        # This is a template - actual implementation depends on database type
        db_type = self.config.options.get('db_type', 'postgresql')
        
        conn_string = self.config.credentials.get('connection_string')
        if not conn_string:
            raise ValueError("connection_string required in credentials")
        
        logger.info(f"Would connect to {db_type} database")
        self.is_connected = True
        return True
    
    def disconnect(self) -> bool:
        if self._connection:
            self._connection.close()
        self.is_connected = False
        return True
    
    def extract(self, table: str, **kwargs) -> Iterator[Dict]:
        query = kwargs.get('query', f"SELECT * FROM {table}")
        
        # Template - actual implementation would execute query
        logger.info(f"Would execute: {query}")
        return iter([])
    
    def get_schema(self, table: str) -> Dict[str, str]:
        # Template - would query information_schema
        return {}


# Connector registry
CONNECTOR_REGISTRY: Dict[str, type] = {
    'file': FileConnector,
    'api': APIConnector,
    'database': DatabaseConnector,
}


def create_connector(connector_type: str, config: ConnectorConfig, **kwargs) -> BaseConnector:
    """Factory function to create connectors."""
    connector_class = CONNECTOR_REGISTRY.get(connector_type)
    if not connector_class:
        raise ValueError(f"Unknown connector type: {connector_type}")
    return connector_class(config, **kwargs)


if __name__ == "__main__":
    # Demo with file connector
    config = ConnectorConfig(
        name="synthetic_data",
        source_system="wbez_donations",
        batch_size=1000,
    )
    
    connector = FileConnector(config, base_path="data/synthetic")
    
    print("Testing FileConnector...")
    try:
        connector.connect()
        result = connector.extract_with_retry("wbez_donations")
        print(f"Result: {result.success}, Records: {result.record_count}")
        connector.disconnect()
    except Exception as e:
        print(f"Expected error (no data yet): {e}")
    
    print("\nConnector metrics:", connector.get_metrics())