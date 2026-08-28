"""Client-side API token management."""
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


class TokenManager:
    """Handles API token management for the client."""

    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self.token_dir = Path("data/tokens")
        self.token_dir.mkdir(parents=True, exist_ok=True)
        self.client_id = load_or_generate_client_id()

    def have_token(self) -> bool:
        """Check if we have an API token stored."""
        token_path = self.token_dir / "api_token.txt"
        return token_path.exists()

    def load_token(self) -> Optional[str]:
        """Load the API token from local storage."""
        token_path = self.token_dir / "api_token.txt"
        if token_path.exists():
            return token_path.read_text(encoding="utf-8").strip()
        return None

    def save_token(self, token: str):
        """Save the API token to local storage."""
        token_path = self.token_dir / "api_token.txt"
        token_path.write_text(token, encoding="utf-8")

    def delete_token(self):
        """Delete the stored API token."""
        token_path = self.token_dir / "api_token.txt"
        if token_path.exists():
            token_path.unlink()

    async def request_new_token(self, description: str = "") -> str:
        """Request a new API token from the server."""
        url = f"{self.server_url}/api/tokens/create"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "client_id": self.client_id,
                    "description": description,
                    "expires_in_days": 30
                }
            )
            response.raise_for_status()
            
            data = response.json()
            token = data["token"]
            
            # Save the token locally
            self.save_token(token)
            
            print(f"✅ New API token created!")
            print(f"   Client ID: {self.client_id}")
            print(f"   Token: {token}")
            print(f"   Expires: {data['expires_at_human']}")
            
            return token

    async def validate_token(self, token: str) -> bool:
        """Validate the token with the server."""
        url = f"{self.server_url}/api/tokens/validate"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if response.status_code == 200:
                return True
            else:
                return False

    async def list_tokens(self):
        """List all tokens for this client."""
        url = f"{self.server_url}/api/tokens/list/{self.client_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            return response.json()

    def get_auth_headers(self, token: Optional[str] = None) -> dict:
        """Get authentication headers for API requests."""
        if token is None:
            token = self.load_token()
        
        if not token:
            return {}
            
        return {
            "Authorization": f"Bearer {token}"
        }