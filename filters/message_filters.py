"""Filter classes to apply over the telegram messages
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class MessageFilter(ABC):
    
    @abstractmethod
    def apply_to_messages(self, messages: List[Dict]) -> List[Dict]:
        ...


    