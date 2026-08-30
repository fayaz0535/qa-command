"""Symmetric encryption for credentials at rest — currently just the ADO PAT.

Fails loudly rather than falling back to plaintext: if ADO_ENCRYPTION_KEY isn't
set, saving or reading a connection raises instead of silently storing the PAT
unencrypted. The rest of the app boots and serves fine either way — only the
ADO connection endpoints are affected until the key is configured.
"""

from cryptography.fernet import Fernet, InvalidToken

from config import ADO_ENCRYPTION_KEY


def _get_fernet() -> Fernet:
    if not ADO_ENCRYPTION_KEY:
        raise RuntimeError(
            "ADO_ENCRYPTION_KEY is not set — refusing to store or read PAT credentials "
            "without encryption. Generate one with:\n"
            "  python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"\n"
            "and set it in .env."
        )
    try:
        return Fernet(ADO_ENCRYPTION_KEY.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "ADO_ENCRYPTION_KEY is not a valid Fernet key — it must be exactly what "
            "Fernet.generate_key() produces."
        ) from exc


def encrypt_secret(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError(
            "Failed to decrypt the stored ADO credential — ADO_ENCRYPTION_KEY may have "
            "changed since it was saved. Reconnect ADO to re-save the PAT."
        ) from exc
