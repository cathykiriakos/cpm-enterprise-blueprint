"""
Metrics Engine - Generates platform-specific SQL from YAML definitions.
Author: Catherine Kiriakos
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class SQLPlatform(Enum):
    STANDARD = "standard"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"


class MetricsEngine:
    """Loads YAML metrics definitions and generates SQL for multiple platforms."""
    
    def __init__(self, config_path: str = "config/metrics_definitions.yaml"):
        self.metrics = {}
        self.metadata = {}
        self._load(config_path)
    
    def _load(self, path: str) -> None:
        if not Path(path).exists():
            return
        with open(path) as f:
            data = yaml.safe_load(f)
        self.metadata = data.get('metadata', {})
        for name, cfg in data.get('metrics', {}).items():
            calc = cfg.get('calculation', {})
            self.metrics[name] = {
                'display_name': cfg.get('display_name', name),
                'category': cfg.get('category', 'uncategorized'),
                'definition': cfg.get('definition', ''),
                'owner': cfg.get('business_owner', 'Unknown'),
                'sql_standard': calc.get('sql_standard'),
                'sql_snowflake': calc.get('sql_snowflake'),
                'sql_databricks': calc.get('sql_databricks'),
                'dimensions': cfg.get('dimensions', []),
                'caveats': cfg.get('caveats', []),
            }
    
    def list_metrics(self, category: str = None) -> List[str]:
        if category:
            return [n for n, m in self.metrics.items() if m['category'] == category]
        return list(self.metrics.keys())
    
    def get_sql(self, name: str, platform: SQLPlatform = SQLPlatform.STANDARD, 
                dimension: str = None) -> str:
        m = self.metrics.get(name)
        if not m:
            raise ValueError(f"Unknown metric: {name}")
        
        sql = m.get(f'sql_{platform.value}') or m.get('sql_standard')
        if not sql:
            raise ValueError(f"No SQL for {name}")
        
        if dimension:
            dim = next((d for d in m['dimensions'] if d.get('name') == dimension), None)
            if dim:
                sql = sql.rstrip().rstrip(';') + '\n' + dim.get('sql_fragment', '')
        
        return sql.strip()
    
    def get_documentation(self, name: str) -> str:
        m = self.metrics.get(name)
        if not m:
            return f"Unknown metric: {name}"
        return f"""
# {m['display_name']}
**Category:** {m['category']}
**Owner:** {m['owner']}

## Definition
{m['definition']}

## Caveats
{chr(10).join('- ' + c for c in m.get('caveats', []))}
"""


if __name__ == "__main__":
    engine = MetricsEngine()
    print("Available metrics:", engine.list_metrics())
    for p in SQLPlatform:
        print(f"\n=== {p.value.upper()} ===")
        try:
            print(engine.get_sql("active_member", p))
        except Exception as e:
            print(f"Error: {e}")