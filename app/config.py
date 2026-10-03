from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data' / 'public'
POLICY_DIR = DATA_DIR / 'policies'
PRODUCT_SPEC_DIR = DATA_DIR / 'products'
RUNTIME_DIR = ROOT_DIR / 'runtime'
STATE_FILE = RUNTIME_DIR / 'state.json'
POLICY_OVERLAY_FILE = RUNTIME_DIR / 'policy_overlay.json'
COMPILED_POLICY_FILE = RUNTIME_DIR / 'compiled_policies.json'

DEFAULT_NOW = '2026-10-03T12:51:00+05:30'

# Auto-load .env file if present in workspace root
_env_path = ROOT_DIR / '.env'
if _env_path.exists():
    try:
        for _line in _env_path.read_text(encoding='utf-8').splitlines():
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                if _k and _k not in os.environ:
                    os.environ[_k] = _v
    except Exception:
        pass

# Free Google Gemini API configuration (replaces legacy ChatGPT/OpenAI adapter)
# Upgraded to state-of-the-art free model: gemini-2.0-flash
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', os.getenv('GOOGLE_API_KEY', os.getenv('LLM_API_KEY', ''))).strip()
GEMINI_MODEL = os.getenv('GEMINI_MODEL', os.getenv('LLM_MODEL', 'gemini-2.0-flash')).strip()
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', os.getenv('LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta')).rstrip('/')

# Aliases for backwards compatibility
LLM_BASE_URL = GEMINI_BASE_URL
LLM_API_KEY = GEMINI_API_KEY
LLM_MODEL = GEMINI_MODEL

APP_NAME = 'NovaMart Guardian'
APP_VERSION = '1.0.0'
