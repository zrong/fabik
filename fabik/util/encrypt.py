""" .._fabik_util_encrypt:

fabik.util.encrypt
~~~~~~~~~~~~~~~~~~~

用于加密的封装
"""
import re
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from fabik.error import EncryptError

ZERO_RE = re.compile(r'[\x00-\x1F]+$')


class AES_CBC(object):
    """使用 AES 进行对称加解密。

    :param key: 密钥。
    :param iv: iv。
    """

    def __init__(self, key, iv):
        self._cipher = Cipher(
            algorithms.AES(key), modes.CBC(iv), backend=default_backend()
        )

    def encrypt(self, plain_txt):
        return None

    def decrypt(self, cipher: str | bytes) -> str:
        decryptor = self._cipher.decryptor()
        if isinstance(cipher, str):
            cipher = cipher.encode()
        plain = decryptor.update(cipher) + decryptor.finalize()
        # 去掉尾部可能存在的 \x00-\x1F
        return ZERO_RE.sub('', plain.decode('utf-8'))

    def decrypt_b64(self, b64_txt) -> str:
        encrypted_bytes = base64.b64decode(b64_txt)
        return self.decrypt(encrypted_bytes)


class Encrypt(object):
    """使用 Fernet 模块进行对称加解密。

    :param key: 密钥。
    """

    @staticmethod
    def fernet_key() -> bytes:
        """生成一个 fernet 密钥。"""
        key = Fernet.generate_key()
        return key

    def __init__(self, key: str) -> None:
        self._factory = Fernet(key.encode())

    def encrypt(self, plain: str | bytes) -> bytes:
        """对提供的 plain_text 进行加密。"""
        if isinstance(plain, str):
            plain = plain.encode()
        return self._factory.encrypt(plain)

    def decrypt(self, cipher: str | bytes) -> bytes:
        """对提供的 cipher_text 进行解密。"""
        if isinstance(cipher, str):
            cipher = cipher.encode()
        try:
            txt = self._factory.decrypt(cipher)
            return txt
        except (InvalidToken, UnicodeDecodeError) as e:
            raise EncryptError(err_type=e, err_msg=f'Invalid Token: {cipher!s}, error: {e!s}')
