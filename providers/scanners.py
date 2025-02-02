from abc import ABC, abstractmethod


class ScannerService(ABC):

    @abstractmethod
    async def run(self):
        ...
