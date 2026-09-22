import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from ...domain.repositories import TokenStore
from ..security.crypto import PasswordCipher, load_or_create_key


class DbTokenStore(TokenStore):
    """API token 加密存储到 SQLite（与配置共用 data/client.db）。

    token 经 PasswordCipher 加密后入库，load_token() 返回明文，
    对 TokenApiService 与调用方透明。构造时一次性迁移旧的
    tokens/api_token.txt 明文文件（导入后删除）。
    """

    def __init__(self, db_path: str = "data/client.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        key_path = Path(self.db_path).parent / ".secret.key"
        self._cipher = PasswordCipher(load_or_create_key(key_path))
        self._init_table()
        self._migrate_legacy_file()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_table(self):
        with self._conn() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS api_token (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    token TEXT NOT NULL DEFAULT '',
                    CHECK (id = 1)
                )
            """)
            db.commit()

    def _migrate_legacy_file(self):
        """导入旧版 FileTokenStore 的明文文件后删除；清理失败仅忽略——
        token 已入库，重复迁移幂等且无功能影响。"""
        legacy = Path(self.db_path).parent / "tokens" / "api_token.txt"
        try:
            if not legacy.exists():
                return
            token = legacy.read_text(encoding="utf-8").strip()
            if token and not self.have_token():
                self.save_token(token)
            legacy.unlink()
            legacy.parent.rmdir()
        except OSError:
            pass

    def have_token(self) -> bool:
        return bool(self.load_token())

    def load_token(self) -> Optional[str]:
        with self._conn() as db:
            row = db.execute("SELECT token FROM api_token WHERE id = 1").fetchone()
        if row and row[0]:
            # 密钥丢失导致解密失败时视为无 token，走重新申请流程
            return self._cipher.decrypt(row[0]) or None
        return None

    def save_token(self, token: str) -> None:
        with self._conn() as db:
            db.execute(
                "INSERT INTO api_token (id, token) VALUES (1, ?)"
                " ON CONFLICT(id) DO UPDATE SET token = excluded.token",
                (self._cipher.encrypt(token),),
            )
            db.commit()

    def delete_token(self) -> None:
        with self._conn() as db:
            db.execute("DELETE FROM api_token WHERE id = 1")
            db.commit()
