import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from src.infrastructure.security.crypto import PasswordCipher, load_or_create_key
from tests.test_simulation_page import _make_config
from src.infrastructure.config.config_service import ConfigService


def _cipher(tmp: Path) -> PasswordCipher:
    return PasswordCipher(load_or_create_key(tmp / ".secret.key"))


class LoadOrCreateKeyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_key_file_once(self):
        path = self.dir / ".secret.key"
        key = load_or_create_key(path)
        self.assertTrue(path.exists())
        self.assertEqual(load_or_create_key(path), key)
        # 同目录两个 cipher 用同一密钥，密文可互换解密
        c1, c2 = PasswordCipher(key), PasswordCipher(key)
        self.assertEqual(c2.decrypt(c1.encrypt("pwd")), "pwd")


class PasswordCipherTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cipher = _cipher(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_roundtrip(self):
        token = self.cipher.encrypt("p@ss 密码123")
        self.assertNotIn("p@ss", token)
        self.assertTrue(token.startswith("enc:v1:"))
        self.assertEqual(self.cipher.decrypt(token), "p@ss 密码123")

    def test_empty_stays_empty(self):
        self.assertEqual(self.cipher.encrypt(""), "")
        self.assertEqual(self.cipher.decrypt(""), "")

    def test_legacy_plaintext_passthrough(self):
        # 历史明文（无前缀）读取时原样返回
        self.assertEqual(self.cipher.decrypt("old-plain-pwd"), "old-plain-pwd")

    def test_wrong_key_returns_empty(self):
        token = self.cipher.encrypt("pwd")
        other = PasswordCipher(Fernet.generate_key())
        self.assertEqual(other.decrypt(token), "")


class ConfigServiceEncryptionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "client.db"
        self.service = ConfigService(str(self.db_path))

    def tearDown(self):
        self._tmp.cleanup()

    def _stored(self, column: str) -> str:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT {column} FROM app_config WHERE id = 1").fetchone()[0]
        finally:
            conn.close()

    def test_passwords_stored_encrypted(self):
        self.service.save(_make_config(
            tq_password="tq-pwd",
            trade_password="trade-pwd",
            database_path=str(self.db_path),
        ))
        for column, plain in [
            ("tq_password", "tq-pwd"),
            ("trade_password", "trade-pwd"),
        ]:
            stored = self._stored(column)
            self.assertTrue(stored.startswith("enc:v1:"), f"{column} 未加密: {stored}")
            self.assertNotIn(plain, stored)

    def test_load_returns_plaintext(self):
        self.service.save(_make_config(
            tq_password="tq-pwd",
            trade_password="trade-pwd",
            database_path=str(self.db_path),
        ))
        loaded = self.service.load()
        self.assertEqual(loaded.tq_password, "tq-pwd")
        self.assertEqual(loaded.trade_password, "trade-pwd")

    def test_legacy_plaintext_db_loads_and_upgrades_on_save(self):
        # 模拟历史明文数据：表结构不变，密码列直接存明文（无 enc:v1: 前缀）
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO app_config (id, server_url, symbols, auto_trade, tq_account, tq_password,"
            " trade_password, initial_balance, database)"
            " VALUES (1, 'http://127.0.0.1:3080', '[\"SHFE.au2510\"]', 0, 'acc', 'plain-tq',"
            " 'plain-trade', 1000000, ?)",
            (str(self.db_path),),
        )
        conn.commit()
        conn.close()

        # 读取：旧明文直通
        loaded = self.service.load()
        self.assertEqual(loaded.tq_password, "plain-tq")
        # 保存：升级为密文
        self.service.save(loaded)
        self.assertTrue(self._stored("tq_password").startswith("enc:v1:"))
        self.assertEqual(self.service.load().tq_password, "plain-tq")

    def test_sim_columns_merged_into_tq_and_dropped(self):
        # 历史库含 sim_account/sim_password 列：仅在模拟页填过（tq 为空）时搬迁进 tq 列，
        # 随后 sim 列被 DROP
        conn = sqlite3.connect(self.db_path)
        conn.execute("ALTER TABLE app_config ADD COLUMN sim_account TEXT NOT NULL DEFAULT ''")
        conn.execute("ALTER TABLE app_config ADD COLUMN sim_password TEXT NOT NULL DEFAULT ''")
        conn.execute(
            "INSERT INTO app_config (id, server_url, symbols, auto_trade, tq_account, tq_password,"
            " sim_account, sim_password, initial_balance, database)"
            " VALUES (1, 'http://127.0.0.1:3080', '[\"SHFE.au2510\"]', 0, '', '',"
            " '13800000000', 'sim-pwd', 1000000, ?)",
            (str(self.db_path),),
        )
        conn.commit()
        conn.close()

        service = ConfigService(str(self.db_path))
        columns = [
            r[1] for r in sqlite3.connect(self.db_path).execute("PRAGMA table_info(app_config)")
        ]
        self.assertNotIn("sim_account", columns)
        self.assertNotIn("sim_password", columns)
        loaded = service.load()
        self.assertEqual(loaded.tq_account, "13800000000")
        self.assertEqual(loaded.tq_password, "sim-pwd")

        # tq 列已有值时不覆盖，sim 值直接随 DROP 丢弃
        conn = sqlite3.connect(self.db_path)
        conn.execute("ALTER TABLE app_config ADD COLUMN sim_account TEXT NOT NULL DEFAULT ''")
        conn.execute("ALTER TABLE app_config ADD COLUMN sim_password TEXT NOT NULL DEFAULT ''")
        conn.execute(
            "UPDATE app_config SET sim_account = 'other', sim_password = 'other-pwd' WHERE id = 1"
        )
        conn.commit()
        conn.close()
        ConfigService(str(self.db_path))  # 触发迁移
        reloaded = service.load()
        self.assertEqual(reloaded.tq_account, "13800000000")

    def test_key_file_created_next_to_db(self):
        self.service.save(_make_config(tq_password="pwd", database_path=str(self.db_path)))
        self.assertTrue((Path(self._tmp.name) / ".secret.key").exists())


if __name__ == "__main__":
    unittest.main()
