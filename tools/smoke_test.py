import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from src.api.openai_client import describe_image
from src.api.ebay_client import search_ebay

print("Running smoke tests")
print("--- OpenAI describe_image (expected mock fallback if image missing or on error) ---")
print(describe_image("nonexistent.jpg"))
print("--- eBay search_ebay (mock or real depending on config) ---")
print(search_ebay("vintage radio", limit=3))
