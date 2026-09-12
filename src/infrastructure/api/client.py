import json
import os
from pathlib import Path
from typing import Optional

import httpx

from ...domain.entities import StrategySignal
from ...domain.repositories import StrategyStreamClient
from ...domain.repositories import TokenStore

class FileTokenStore(TokenStore):
    def __init__(self, token_dir: Path | str = "data/tokens"):
        self.token_dir = Path(token_dir)
        self.token_dir.mkdir(parents=True, exist_ok=True)

    def have_token(self) -> bool:
        return (self.token_dir / "api_token.txt").exists()

    def load_token(self) -> Optional[str]:
        token_path = self.token_dir / "api_token.txt"
        if token_path.exists():
            return token_path.read_text(encoding="utf-8").strip()
        return None

    def save_token(self, token: str) -> None:
        (self.token_dir / "api_token.txt").write_text(token, encoding="utf-8")

    def delete_token(self) -> None:
        token_path = self.token_dir / "api_token.txt"
        if token_path.exists():
            token_path.unlink()

class TokenApiService:
    def __init__(self, server_url: str, token_store: TokenStore, client_id: str):
        self.server_url = server_url.rstrip("/")
        self.token_store = token_store
        self.client_id = client_id

    async def request_new_token(self, description: str = "") -> str:
        url = f"{self.server_url}/api/tokens/create"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "client_id": self.client_id,
                    "description": description,
                    "expires_in_days": 90,
                },
            )
            response.raise_for_status()
            data = response.json()
            token = data["token"]
            self.token_store.save_token(token)
            return token

    async def validate_token(self, token: str) -> bool:
        url = f"{self.server_url}/api/tokens/validate"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.status_code == 200

    async def list_tokens(self):
        url = f"{self.server_url}/api/tokens/list/{self.client_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def get_auth_headers(self, token: Optional[str] = None) -> dict:
        if token is None:
            token = self.token_store.load_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

class ServerStreamClient(StrategyStreamClient):
    def __init__(
        self,
        server_url: str,
        symbols: list[str],
        token_service: TokenApiService | None = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.symbols = symbols
        self.token_service = token_service

    async def stream(self):
        symbols = ",".join(self.symbols)
        url = f"{self.server_url}/api/stream?symbols={symbols}"

        headers = {"Accept": "text/event-stream"}
        if self.token_service is not None:
            headers.update(self.token_service.get_auth_headers())

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                event = None
                data = None
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        event = line[6:].strip()
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                    elif not line:
                        if event == "trading_result" and data:
                            yield StrategySignal(**json.loads(data))
                        event = None
                        data = None
