"""
Configuration module for EquiPath.
Loads environment variables from .env file safely.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file (look in project root)
env_path = Path(__file__).parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)


def get_anthropic_api_key():
    """
    Get Anthropic API key from environment.

    Returns:
    --------
    str or None
        API key if found, None otherwise
    """
    return os.getenv('ANTHROPIC_API_KEY')


def get_anthropic_model():
    """
    Get Anthropic model to use.

    Returns:
    --------
    str
        Model name (defaults to claude-3-haiku-20240307)
    """
    return os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')


# Load on import
ANTHROPIC_API_KEY = get_anthropic_api_key()
ANTHROPIC_MODEL = get_anthropic_model()


if __name__ == "__main__":
    print("Configuration Test")
    print("=" * 60)

    api_key = get_anthropic_api_key()
    if api_key:
        masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
        print(f"✅ Anthropic API Key found: {masked_key}")
    else:
        print("❌ No Anthropic API Key found")
        print("\nTo set up:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your API key to .env")
        print("  3. Never commit .env to git!")

    print(f"\nModel: {get_anthropic_model()}")
    print("\n" + "=" * 60)
