import requests
from typing import Any, Dict, List, Optional, Union

class SakenowaClient:
    BASE_URL = "https://muro.sakenowa.com/sakenowa-data/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _get_json(self, endpoint: str) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        print(f"Fetching {url}...")
        try:
            res = requests.get(url, timeout=self.timeout)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            raise

    def get_areas(self) -> List[Dict[str, Any]]:
        # JSON: {"areas": [{"id": 1, "name": "...", ...}, ...]}
        data = self._get_json("areas")
        return data.get("areas", []) if isinstance(data, dict) else data

    def get_breweries(self) -> List[Dict[str, Any]]:
        # JSON: {"breweries": [{"id": 1, "name": "...", ...}, ...]}
        data = self._get_json("breweries")
        return data.get("breweries", []) if isinstance(data, dict) else data

    def get_brands(self) -> List[Dict[str, Any]]:
        # JSON: {"brands": [{"id": ..., ...}, ...]}
        data = self._get_json("brands")
        return data.get("brands", []) if isinstance(data, dict) else data

    def get_flavor_charts(self) -> List[Dict[str, Any]]:
        # JSON: {"flavorCharts": [...]}
        data = self._get_json("flavor-charts")
        return data.get("flavorCharts", []) if isinstance(data, dict) else data

    def get_tags(self) -> List[Dict[str, Any]]:
        # JSON: {"tags": [{"id": ..., "tag": ...}, ...]}
        data = self._get_json("flavor-tags")
        return data.get("tags", []) if isinstance(data, dict) else data

    def get_brand_tags(self) -> List[Dict[str, Any]]:
        # JSON: {"flavorTags": [{"brandId": ..., "tagIds": [...]}, ...]}
        data = self._get_json("brand-flavor-tags")
        return data.get("flavorTags", []) if isinstance(data, dict) else data

    def get_rankings(self) -> List[Dict[str, Any]]:
        # JSON: {"yearMonth": 202301, "overall": [...], ...} (Single object)
        # OR {"rankings": [...]} (List wrapper)
        # OR [...] (List)
        data = self._get_json("rankings")
        
        ranking_list = []
        if isinstance(data, dict):
            if "overall" in data and "yearMonth" in data:
                ranking_list.append(data)
            elif "rankings" in data:
                ranking_list = data["rankings"]
        elif isinstance(data, list):
            ranking_list = data
            
        return ranking_list
