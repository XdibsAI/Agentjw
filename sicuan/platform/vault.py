"""
Secret Vault - API key terenkripsi
"""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecretVault:
    """Vault terenkripsi untuk API keys"""

    def __init__(self):
        self.vault_dir = Path("/home/dibs/agentjw/memory/keys")
        self.vault_dir.mkdir(exist_ok=True)
        self._init_cipher()

    def _init_cipher(self):
        """Initialize encryption"""
        master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not master_key:
            salt = b"sicuan_salt_2026"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b"sicuan_master_secret"))
            self.cipher = Fernet(key)
        else:
            self.cipher = Fernet(master_key.encode())

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted.encode()).decode()

    def save_secret(self, workspace_id: str, provider: str, api_key: str) -> str:
        """Save encrypted API key"""
        secret_id = f"{workspace_id}_{provider}"
        encrypted = self.encrypt(api_key)
        
        secret_file = self.vault_dir / f"{secret_id}.enc"
        secret_file.write_text(encrypted)
        return secret_id

    def get_secret(self, workspace_id: str, provider: str) -> str:
        """Get decrypted API key"""
        secret_id = f"{workspace_id}_{provider}"
        secret_file = self.vault_dir / f"{secret_id}.enc"
        
        if not secret_file.exists():
            return None
        
        encrypted = secret_file.read_text()
        return self.decrypt(encrypted)


def get_vault():
    _vault = None
    if _vault is None:
        _vault = SecretVault()
    return _vault
