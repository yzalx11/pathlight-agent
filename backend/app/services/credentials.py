import keyring


SERVICE_NAME = "pathlight-agent"
DEEPSEEK_KEY_NAME = "deepseek-api-key"


def save_deepseek_key(api_key: str) -> None:
    keyring.set_password(SERVICE_NAME, DEEPSEEK_KEY_NAME, api_key)


def get_deepseek_key() -> str | None:
    return keyring.get_password(SERVICE_NAME, DEEPSEEK_KEY_NAME)


def has_deepseek_key() -> bool:
    return bool(get_deepseek_key())
