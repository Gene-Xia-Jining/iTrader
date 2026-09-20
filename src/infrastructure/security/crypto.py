from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

# 密文前缀：标识加密版本，用于兼容历史明文数据（无前缀 = 旧明文，读取时直通）
_PREFIX = "enc:v1:"


def load_or_create_key(key_path: Path) -> bytes:
    """读取密钥文件，不存在时生成新密钥并写入。"""
    key_path = Path(key_path)
    if key_path.exists():
        return key_path.read_bytes().strip()
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    try:
        # Windows 上对普通文件意义有限，失败不影响功能
        key_path.chmod(0o600)
    except OSError:
        pass
    return key


class PasswordCipher:
    """密码字段的可逆加解密：Fernet（AES-128-CBC + HMAC-SHA256 完整性校验）。

    密钥文件与应用数据同机存放，防护目标是避免 SQLite 文件中出现明文密码，
    而非对抗能同时拿到密钥文件的攻击者。
    """

    def __init__(self, key: bytes):
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return _PREFIX + token

    def decrypt(self, stored: str) -> str:
        if not stored:
            return ""
        if not stored.startswith(_PREFIX):
            # 历史明文：下次 save() 时会加密升级
            return stored
        try:
            return self._fernet.decrypt(stored[len(_PREFIX):].encode("ascii")).decode("utf-8")
        except InvalidToken:
            # 密钥丢失/更换后旧密文不可解，返回空串避免启动链崩溃，用户重填即可
            return ""
