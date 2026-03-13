from src.api.mock_openai import describe_image_mock
from src.api.mock_ebay import search_ebay_mock


REQUIRED_IMAGE_KEYS = [
    "brand",
    "model",
    "category",
    "condition",
    "features",
    "estimated_value_range",
    "grading_notes",
]


def test_describe_image_mock_shape():
    result = describe_image_mock("anything.jpg")
    assert isinstance(result, dict)
    assert all(key in result for key in REQUIRED_IMAGE_KEYS)
    assert isinstance(result["features"], list)


def test_search_ebay_mock_returns_limited_results():
    results = search_ebay_mock("MacBook Air", limit=3)
    assert len(results) == 3
    assert all("title" in item and "price" in item and "url" in item for item in results)
    assert all(isinstance(item["price"], float) for item in results)


def test_describe_image_mock_supports_multi_card_shape():
    result = describe_image_mock("multi_cards.jpg")
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) >= 2


def test_describe_image_mock_filename_overrides():
    cheap = describe_image_mock('cheap_card.jpg')
    expensive = describe_image_mock('expensive_card.jpg')

    assert 'card' in cheap['category'].lower()
    assert isinstance(cheap['grading_notes'], list)
    assert 'card' in expensive['category'].lower()


def test_search_ebay_mock_supports_price_tiers_for_cards():
    cheap = search_ebay_mock('cheap common base card', limit=5)
    premium = search_ebay_mock('premium limited rookie auto /99', limit=5)

    cheap_median = sorted([r['price'] for r in cheap])[len(cheap)//2]
    premium_median = sorted([r['price'] for r in premium])[len(premium)//2]

    assert cheap_median < 20
    assert premium_median >= 20
