import unicodedata


def normalize_name(text: str):
    if not text: return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def normalize_branch_name(text: str) -> str:
    return normalize_name(text)


def normalize_user_name(s: str):
    if not s: return ""
    return s.strip().title()
