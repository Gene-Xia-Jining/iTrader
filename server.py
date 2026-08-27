import json
import httpx

from .models import TradingResult


class ServerClient:

    def __init__(
        self,
        server_url: str,
        symbols: list[str],
    ):
        self.server_url = server_url.rstrip("/")
        self.symbols = symbols

    async def stream(self):

        symbols = ",".join(
            self.symbols
        )

        url = (
            f"{self.server_url}"
            f"/api/stream"
            f"?symbols={symbols}"
        )

        async with httpx.AsyncClient(
            timeout=None
        ) as client:

            async with client.stream(
                "GET",
                url,
                headers={
                    "Accept": "text/event-stream"
                },
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