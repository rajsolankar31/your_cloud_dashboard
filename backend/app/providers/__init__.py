from .custom import CustomProvider
from .google import GoogleProvider
from .oracle import OracleProvider
from .vercel import VercelProvider

REGISTRY = {p.key: p for p in (OracleProvider(), GoogleProvider(), VercelProvider(), CustomProvider())}
