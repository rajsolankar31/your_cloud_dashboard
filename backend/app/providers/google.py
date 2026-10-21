from ..config import use_mock
from . import mock
from .base import Provider, ProviderError

NOT_READY = "Live Google Cloud adapter is not implemented yet (roadmap Phase 3)."


class GoogleProvider(Provider):
    key, label = "google", "Google Cloud"
    actions = {"compute_instance": ["start", "stop"]}

    def configured(self) -> bool:
        return False  # Phase 3: will check GOOGLE_APPLICATION_CREDENTIALS

    def list_resources(self):
        if use_mock():
            return mock.resources(self.key)
        raise ProviderError(NOT_READY)

    def execute(self, action, resource):
        if not use_mock():
            raise ProviderError(NOT_READY)
        native = resource["id"].split(":", 1)[1]
        mock.set_status(self.key, native, "running" if action == "start" else "stopped")
        return {"detail": f"mock {action} applied"}
