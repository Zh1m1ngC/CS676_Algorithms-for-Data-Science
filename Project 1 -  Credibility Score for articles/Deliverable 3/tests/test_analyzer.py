# tests/test_analyzer.py

# Import the function we want to test
from credibility_analyzer import calculate_rule_based_score

def test_clickbait_headline_penalty():
    """
    Tests if a clickbait headline correctly applies a score penalty.
    """
    # A short, dummy text for the article body
    dummy_text = "This is some sample text for the article. " * 20

    # A clearly clickbait title
    clickbait_title = "You Won't Believe What Happens Next!"

    # Run the function with the clickbait title
    score, explanations = calculate_rule_based_score(text=dummy_text, title=clickbait_title)

    # Assert that the score is less than the neutral starting score of 50
    assert score < 50

    # Optional: Check if the explanation text is present
    has_clickbait_explanation = any("clickbait" in exp.lower() for exp in explanations)
    assert has_clickbait_explanation is True