import base64
from pathlib import Path
from typing import Optional

import httpx

from ...domain.repositories import CertificateStore


def load_or_generate_client_id() -> str:
    id_path = Path("data/client_id.txt")
    if id_path.exists():
        return id_path.read_text(encoding="utf-8").strip()
    import uuid
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    id_path.parent.mkdir(parents=True, exist_ok=True)
    id_path.write_text(client_id, encoding="utf-8")
    return client_id


def generate_key_and_csr(client_id: str):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, client_id)]))
        .sign(key, hashes.SHA256())
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM)
    return key_pem, csr_pem, key


class FileCertificateStore(CertificateStore):
    def __init__(self, cert_dir: Path | str = "data/certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def have_cert(self) -> bool:
        return (
            (self.cert_dir / "client.key").exists()
            and (self.cert_dir / "client.crt").exists()
        )

    def client_cert_path(self) -> str:
        return str(self.cert_dir / "client.crt")

    def client_key_path(self) -> str:
        return str(self.cert_dir / "client.key")

    def ca_cert_path(self) -> str:
        return str(self.cert_dir / "ca.crt")


class CertificateEnrollmentService:
    def __init__(
        self,
        enrollment_url: str,
        store: CertificateStore | None = None,
        client_id: str | None = None,
        ca_cert_path: str = "",
    ):
        self.enrollment_url = enrollment_url.rstrip("/")
        self.store = store or FileCertificateStore()
        self.client_id = client_id or load_or_generate_client_id()
        self.ca_cert_path = ca_cert_path

    def have_cert(self) -> bool:
        return self.store.have_cert()

    async def enroll(self, contact: str = "", note: str = "") -> Optional[str]:
        key_pem, csr_pem, _ = generate_key_and_csr(self.client_id)
        key_path = Path(self.store.client_key_path())
        key_path.write_bytes(key_pem)
        key_path.chmod(0o600)

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
        except Exception:
            return None

    async def check_status(self, request_id: str) -> Optional[str]:
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
                    Path(self.store.client_cert_path()).write_bytes(cert_pem)
                    ca_path = Path(self.store.ca_cert_path())
                    if not ca_path.exists():
                        await self.fetch_ca_cert()
                    return "approved"
                elif result["status"] == "rejected":
                    return "rejected"
                else:
                    return "pending"
        except Exception:
            return None

    async def fetch_ca_cert(self):
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.get(
                    f"{self.enrollment_url}/api/cert/ca",
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    Path(self.store.ca_cert_path()).write_bytes(resp.content)
        except Exception:
            pass
