import json
import httpx
import ssl
from pathlib import Path

from .models import TradingResult
from .token_manager import TokenManager


class ServerClient:

    def __init__(
        self,
        server_url: str,
        symbols: list[str],
        token_manager: TokenManager | None = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.symbols = symbols
        self.token_manager = token_manager or TokenManager(server_url)

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=None)

    async def stream(self):

        symbols = ",".join(
            self.symbols
        )

        url = (
            f"{self.server_url}"
            f"/api/stream"
            f"?symbols={symbols}"
        )

        # Get authentication headers
        auth_headers = self.token_manager.get_auth_headers()
        headers = {
            "Accept": "text/event-stream",
            **auth_headers
        }

        async with self._make_client() as client:

            async with client.stream(
                "GET",
                url,
                headers=headers,
            ) as response:

                response.raise_for_status()

                event = None
                data = None

                async for line in response.aiter_lines():

                    if line.startswith("event:"):

                        event = (
                            line[6:].strip()
                        )

                    elif line.startswith("data:"):

                        data = (
                            line[5:].strip()
                        )

                    elif not line:

                        if (
                            event == "trading_result"
                            and data
                        ):

                            yield TradingResult(
                                **json.loads(data)
                            )

                        event = None
                        data = None