from sqlalchemy import Column, String, Text, DateTime, JSON
from models.base import BaseModel


class ADOConnection(BaseModel):
    """Singleton row — Phase 2 supports exactly one ADO connection. encrypted_pat is
    ciphertext only (services/crypto.py); it is never selected into an API response."""
    __tablename__ = "ado_connections"

    org_url = Column(String(500), nullable=False)
    project = Column(String(255), nullable=False)
    encrypted_pat = Column(Text, nullable=False)
    wiql_query = Column(Text, nullable=True)  # None -> config.DEFAULT_ADO_WIQL
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_summary = Column(JSON, nullable=True)
