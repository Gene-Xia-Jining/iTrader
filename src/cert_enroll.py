"""Client certificate enrollment and management."""
import base64
import json
import os
from pathlib import Path
from typing import Optional

import httpx


def load_or_generate_client_id() -> str:
    """Read client_id from local file or generate a unique one."""
    id_path = Path("data/client_id.txt")
    if id_path.exists():
        return id_path.read_text(encoding="utf-8").strip()
    import uuid
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    id_path.parent.mkdir(parents=True, exist_ok=True)
    id_path.write_text(client_id, encoding="utf-8")
    return client_id


class CertManager:
    """Handles client certificate enrollment and mTLS configuration."""

    def __init__(self, enrollment_url: str, ca_cert_path: str = ""):
        self.enrollment_url = enrollment_url.rstrip("/")
        self.ca_cert_path = ca_cert_path
        self.cert_dir = Path("data/certs")
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        self.client_id = load_or_generate_client_id()

    def have_cert(self) -> bool:
        """Check if we have a client certificate."""
        return (
            (self.cert_dir / "client.key").exists()
            and (self.cert_dir / "client.crt").exists()
        )

    def get_mtls_context(self) -> httpx.Client | httpx.AsyncClient:
        """Return httpx client configured for mTLS."""
        ca_cert = self.ca_cert_path or str(self.cert_dir / "ca.crt")
        if not os.path.exists(ca_cert):
            raise FileNotFoundError(f"CA certificate not found at {ca_cert}")
        key = str(self.cert_dir / "client.key")
        cert = str(self.cert_dir / "client.crt")
        if not os.path.exists(key) or not os.path.exists(cert):
            raise FileNotFoundError("Client certificate missing")
        return httpx.Client(
            verify=ca_cert,
            cert=(cert, key),
        )

    async def enroll(self, contact: str = "", note: str = "") -> Optional[str]:
        """Submit enrollment request and return request_id."""
        from cryptography.hazmat.primitives import serialization
        from pki_client import generate_key_and_csr

        key_pem, csr_pem, _ = generate_key_and_csr(self.client_id)
        # save private key
        key_path = self.cert_dir / "client.key"
        key_path.write_bytes(key_pem)
        key_path.chmod(0o600)

        # submit CSR
        csr_b64 = base64.b64encode(csr_pem).decode()
        data = {
            "client_id": self.client_id,
            "csr_pem": csr_b64,
            "contact": contact,
            "note": note,
        }
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.post(
                    f"{self.enrollment_url}/api/cert/enroll",
                    json=data,
                    timeout=30.0,
                )
                resp.raise_for_status()
                result = resp.json()
                return result["request_id"]
        except Exception as e:
            print(f"Enrollment failed: {e}")
            return None

    async def check_status(self, request_id: str) -> Optional[str]:
        """Poll enrollment status; if approved, download and save certificate."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.enrollment_url}/api/cert/status/{request_id}",
                    timeout=10.0,
                )
                resp.raise_for_status()
                result = resp.json()
                if result["status"] == "approved" and result.get("cert_pem"):
                    cert_pem = result["cert_pem"].encode()
                    cert_path = self.cert_dir / "client.crt"
                    cert_path.write_bytes(cert_pem)
                    print(f"Certificate saved to {cert_path}")
                    # also download CA cert if not present
                    ca_path = self.cert_dir / "ca.crt"
                    if not ca_path.exists():
                        await self.fetch_ca_cert()
                    return "approved"
                elif result["status"] == "rejected":
                    return "rejected"
                else:
                    return "pending"
        except Exception as e:
            print(f"Status check failed: {e}")
            return None

    async def fetch_ca_cert(self):
        """Download CA certificate from server (public endpoint)."""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.enrollment_url}/api/cert/ca",
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    ca_pem = resp.content
                    (self.cert_dir / "ca.crt").write_bytes(ca_pem)
                    print("CA certificate downloaded")
                else:
                    # fallback: try /api/health to see if server is up
                    pass
        except Exception:
            pass


# ---------- standalone helpers ----------

def generate_key_and_csr(client_id: str):
    """Generate key and CSR (moved from pki_client)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import serialization

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, client_id),
        ]))
        .sign(key, hashes.SHA256())
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM)
    return key_pem, csr_pem, key
