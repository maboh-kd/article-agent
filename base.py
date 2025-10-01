from typing import List
from ..types import TrendItem

class TrendSource:
    name = "base"
    def fetch(self, limit: int = 5) -> List[TrendItem]:
        raise NotImplementedError
