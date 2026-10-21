from abc import ABC, abstractmethod

from ..config import use_mock


class ProviderError(Exception):
    pass


class Provider(ABC):
    key: str
    label: str
    # resource_type -> actions this adapter has implemented
    actions: dict[str, list[str]] = {}

    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    def list_resources(self) -> list[dict]: ...

    @abstractmethod
    def execute(self, action: str, resource: dict) -> dict: ...

    def mode(self) -> str:
        if use_mock():
            return "mock"
        return "live" if self.configured() else "unconfigured"
