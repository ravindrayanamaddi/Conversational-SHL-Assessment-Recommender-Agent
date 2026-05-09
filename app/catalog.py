import json
from pathlib import Path
from typing import List, Dict

class SHLCatalog:
    def __init__(self):
        self.data: List[Dict] = self._load_catalog()

    def _load_catalog(self) -> List[Dict]:
        path = Path("data/catalog.json")
        if not path.exists():
            raise FileNotFoundError("❌ data/catalog.json not found!")

        data = json.loads(path.read_text(encoding="utf-8"))
        
        # Handle if wrapped in dict
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not isinstance(data, list):
            raise ValueError("Catalog root must be a list")

        print(f"✅ Successfully loaded {len(data)} SHL Individual Assessments")
        return data

    def get_all(self):
        return self.data

catalog = SHLCatalog()