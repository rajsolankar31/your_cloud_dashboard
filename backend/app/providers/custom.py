from .base import Provider, ProviderError


class CustomProvider(Provider):
    """Resources the user adds by hand (any host, e.g. a VPS or a domain)."""
    key, label = "custom", "Manual entries"

    def configured(self): return True
    def mode(self): return "manual"
    def list_resources(self): return []

    def execute(self, action, resource):
        raise ProviderError("Manual entries have no provider API.")
