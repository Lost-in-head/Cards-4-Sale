"""
Mock OpenAI client for development
Returns realistic dummy data for testing without API keys
"""
import random
from pathlib import Path
from typing import Dict


def _add_grading_notes(item: Dict, notes):
    item["grading_notes"] = notes
    return item


def describe_image_mock(image_path: str) -> Dict:
    """
    Return mock image analysis data.
    In production, this would call OpenAI Vision API.
    """
    name = Path(image_path).name.lower()

    if any(token in name for token in ["multi", "lot", "cards"]):
        return {
            "cards": [
                {
                    "brand": "Topps",
                    "model": "Shohei Ohtani Rookie Card",
                    "category": "Sports Trading Cards",
                    "condition": "Near Mint",
                    "features": ["2018 Topps Update", "Card #US1", "Angels"],
                    "estimated_value_range": "$120-220",
                    "grading_notes": ["Slight whitening on bottom-left corner", "Minor print line on front surface"],
                    "player_name": "Shohei Ohtani",
                    "set_name": "Topps Update",
                    "year": "2018",
                    "card_number": "US1",
                    "grade": "Ungraded",
                },
                {
                    "brand": "Topps",
                    "model": "Aaron Judge Rookie Card",
                    "category": "Sports Trading Cards",
                    "condition": "Very Good",
                    "features": ["2017 Topps", "Card #287", "Yankees"],
                    "estimated_value_range": "$40-90",
                    "grading_notes": ["Edge wear on right side", "Small surface scratch near logo"],
                    "player_name": "Aaron Judge",
                    "set_name": "Topps",
                    "year": "2017",
                    "card_number": "287",
                    "grade": "Ungraded",
                }
            ]
        }

    if "cheap" in name:
        return _add_grading_notes({
            "brand": "Topps",
            "model": "Common Base Card",
            "category": "Sports Trading Cards",
            "condition": "Good",
            "features": ["Base set", "Ungraded", "Modern era"],
            "estimated_value_range": "$3-12",
            "player_name": "Prospect Player",
            "set_name": "Topps Base",
            "year": "2022",
            "card_number": "145",
            "grade": "Ungraded",
        }, ["Noticeable corner whitening", "Faint vertical surface scratches"])

    if "expensive" in name or "premium" in name:
        return _add_grading_notes({
            "brand": "Panini",
            "model": "Limited Rookie Auto /99",
            "category": "Sports Trading Cards",
            "condition": "Near Mint",
            "features": ["Serial numbered /99", "On-card autograph", "Sleeved"],
            "estimated_value_range": "$80-180",
            "player_name": "Star Rookie",
            "set_name": "Panini Select",
            "year": "2021",
            "card_number": "RPA-12",
            "grade": "Ungraded",
        }, ["Very minor soft corner on top right", "Clean surface with light print speck"])

    mock_items = [
        _add_grading_notes({
            "brand": "Apple",
            "model": "MacBook Air M2 2023",
            "category": "Electronics > Computers",
            "condition": "Like New",
            "features": ["13-inch display", "16GB RAM", "256GB SSD", "Silver"],
            "estimated_value_range": "$800-1000"
        }, ["No major flaws visible", "Minor cosmetic wear near edge"]) ,
        _add_grading_notes({
            "brand": "Sony",
            "model": "WH-1000XM4 Headphones",
            "category": "Electronics > Audio",
            "condition": "Very Good",
            "features": ["Noise cancelling", "Wireless", "30hr battery", "Black"],
            "estimated_value_range": "$250-350"
        }, ["Light scuffing on earcup", "Padding looks slightly compressed"]),
        _add_grading_notes({
            "brand": "Canon",
            "model": "EOS R6 DSLR Camera",
            "category": "Photography > Cameras",
            "condition": "Good",
            "features": ["20MP full-frame", "4K video", "Mirrorless", "Body only"],
            "estimated_value_range": "$1500-1800"
        }, ["Small body scratches near grip", "Lens mount wear visible"]),
        _add_grading_notes({
            "brand": "Patagonia",
            "model": "Down Jacket",
            "category": "Clothing > Outerwear",
            "condition": "Very Good",
            "features": ["Size Large", "Lightweight", "Blue", "Water resistant"],
            "estimated_value_range": "$100-150"
        }, ["Minor pilling near cuffs", "No tears observed"]),
        _add_grading_notes({
            "brand": "Dyson",
            "model": "V15 Vacuum",
            "category": "Home & Garden > Cleaning",
            "condition": "Like New",
            "features": ["Cordless", "HEPA filter", "60 min runtime", "Silver"],
            "estimated_value_range": "$400-550"
        }, ["Light scratches on wand", "Dust bin appears clean"]),
    ]

    return random.choice(mock_items)
