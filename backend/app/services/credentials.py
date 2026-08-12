import keyring


SERVICE_NAME = "employ-agent"
DEEPSEEK_KEY_NAME = "deepseek-api-key"


def save_deepseek_key(api_key: str) -> None:
    keyring.set_password(SERVICE_NAME, DEEPSEEK_KEY_NAME, api_key)


def has_deepseek_key() -> bool:
    return bool(keyring.get_password(SERVICE_NAME, DEEPSEEK_KEY_NAME))
