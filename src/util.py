import re


def normalize_player_name(name: str) -> str:
    name = str(name).lower()
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", name)
    name = re.sub(r"[^a-z0-9]+", "", name)
    return name
