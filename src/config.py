from pydantic import BaseModel


class Config(BaseModel):

    server_url: str

    symbols: list[str]

    auto_trade: bool = False

    tq_account: str

    tq_password: str

    initial_balance: float = 10_000_000


def load_config(config_path: str = "config.toml"):
    """加载配置文件"""
    import tomllib
    with open(config_path, "rb") as f:
        config_dict = tomllib.load(f)
    return Config(**config_dict)


def save_config(config: Config, config_path: str = "config.toml"):
    """保存配置文件"""
    import toml
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(config.dict(), f)