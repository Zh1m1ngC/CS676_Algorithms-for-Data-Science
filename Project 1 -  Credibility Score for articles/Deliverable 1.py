import re
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from urllib.parse import urlparse

# ... the rest of your code

# --- Configuration ---

# Define weights for combining the two scoring methods. They must sum to 1.0.
RULE_BASED_WEIGHT = 0.5
ML_BASED_WEIGHT = 0.5

# Define lists of example domains for the rule-based engine.
HIGH_CREDIBILITY_DOMAINS = [
    'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'pbs.org',
    'nytimes.com', 'wsj.com', 'washingtonpost.com', 'theguardian.com',
    '.gov', '.edu', 'nature.com', 'sciencemag.org'
]

LOW_CREDIBILITY_DOMAINS = [
    'infowars.com', 'breitbart.com', 'dailycaller.com', 'thegatewaypundit.com',
    'naturalnews.com', 'worldnewsdailyreport.com' # Satire site
]

# --- Component 1: Rule-Based Engine ---

def calculate_rule_based_score(text, url=None):
    """
    Calculates a credibility score based on a set of predefined rules.
    
    Args:
        text (str): The text content of the article.
        url (str, optional): The URL of the article. Defaults to None.
        
    Returns:
        tuple: A tuple containing the score (0-100) and a list of explanation strings.
    """
    score = 50  # Start with a neutral score
    explanations = []
    
    # Rule 1: Source Reputation (only if URL is provided)
    if url:
        domain = urlparse(url).netloc
        domain_check = False
        for high_cred_domain in HIGH_CREDIBILITY_DOMAINS:
            if domain.endswith(high_cred_domain):
                score += 25
                explanations.append(f"[+25] Source Reputation: Domain '{domain}' is on the high credibility list.")
                domain_check = True
                break
        if not domain_check:
            for low_cred_domain in LOW_CREDIBILITY_DOMAINS:
                if domain.endswith(low_cred_domain):
                    score -= 30
                    explanations.append(f"[-30] Source Reputation: Domain '{domain}' is on the low credibility list.")
                    domain_check = True
                    break
        if not domain_check:
             explanations.append("[+/- 0] Source Reputation: Domain is not on predefined lists.")


    # Rule 2: Presence of Author
    # A simple check for common author bylines.
    if re.search(r'\b(by|author)\b', text[:500], re.IGNORECASE):
        score += 10
        explanations.append("[+10] Author Presence: An author byline was found.")
    else:
        score -= 5
        explanations.append("[-5] Author Presence: No clear author byline detected.")

    # Rule 3: Presence of Citations/Sources
    if re.search(r'\b(sources|references|citations|bibliography)\b', text, re.IGNORECASE):
        score += 15
        explanations.append("[+15] Citations: The article appears to cite its sources.")
    else:
        explanations.append("[+/- 0] Citations: No dedicated sources section found.")

    # Rule 4: Sensationalism (e.g., excessive caps or exclamation points)
    num_all_caps = len(re.findall(r'\b[A-Z]{4,}\b', text))
    num_exclamations = text.count('!')
    
    if num_all_caps > 5 or num_exclamations > 5:
        penalty = min((num_all_caps + num_exclamations - 10) * 2, 20) # Cap penalty at 20
        score -= penalty
        explanations.append(f"[-{penalty}] Sensationalism: Excessive use of ALL CAPS or '!' detected.")
    else:
        explanations.append("[+/- 0] Sensationalism: Language appears temperate.")

    # Normalize score to be between 0 and 100
    final_score = max(0, min(100, score))
    return final_score, explanations


# --- Component 2: ML-Based Engine (Simulated with TextBlob) ---

def calculate_ml_score(text):
    """
    Analyzes text for linguistic cues of credibility using TextBlob.
    This simulates a more complex machine learning model.
    
    Args:
        text (str): The text content of the article.
        
    Returns:
        tuple: A tuple containing the score (0-100) and a list of explanation strings.
    """
    explanations = []
    
    if not text.strip():
        return 0, ["[-100] Text Content: No text was provided or could be extracted."]

    blob = TextBlob(text)
    
    # Metric 1: Subjectivity (0.0 is very objective, 1.0 is very subjective)
    # Credible sources are generally more objective.
    subjectivity = blob.sentiment.subjectivity
    
    # We map subjectivity to a score. Low subjectivity = high score.
    subjectivity_score = (1 - subjectivity) * 100
    
    if subjectivity > 0.6:
        explanations.append(f"Analysis: High Subjectivity ({subjectivity:.2f}). The text seems to be heavily opinion-based.")
    elif subjectivity < 0.3:
        explanations.append(f"Analysis: High Objectivity ({subjectivity:.2f}). The text appears to be fact-based.")
    else:
        explanations.append(f"Analysis: Moderate Subjectivity ({subjectivity:.2f}). A mix of facts and opinion.")

    # Metric 2: Polarity (measures sentiment, -1.0 to 1.0)
    # Highly emotional (very positive or negative) language can indicate bias.
    polarity = abs(blob.sentiment.polarity) # Use absolute value to measure distance from neutral (0)
    
    # We map polarity to a score. Low polarity (closer to neutral) = high score.
    polarity_score = (1 - polarity) * 100
    
    if polarity > 0.5:
        explanations.append(f"Analysis: Strong Sentiment ({blob.sentiment.polarity:.2f}). The language is highly emotional, which may indicate bias.")
    else:
        explanations.append(f"Analysis: Neutral Sentiment ({blob.sentiment.polarity:.2f}). The tone is relatively neutral.")

    # Average the two metrics for the final ML score
    final_score = (subjectivity_score + polarity_score) / 2
    return max(0, min(100, final_score)), explanations


# --- Utility Functions ---

def get_article_text_from_url(url):
    """
    Fetches and extracts the main text content from a URL.
    
    Args:
        url (str): The URL of the article.
        
    Returns:
        str: The extracted text, or None if an error occurs.
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # A simple algorithm to find the main content: get text from all paragraphs
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

# --- Main Controller ---

def analyze_credibility(user_input):
    """
    Main function to analyze input (URL or text) and return a credibility score.
    """
    text = ""
    url = None
    
    # Check if input is a URL
    if user_input.startswith('http://') or user_input.startswith('https://'):
        url = user_input
        print("Fetching and parsing article text from URL...")
        text = get_article_text_from_url(url)
        if not text:
            print("Could not retrieve content from the URL.")
            return
    else:
        text = user_input

    if len(text) < 100:
        print("Input text is too short for a meaningful analysis.")
        return

    # 1. Get Rule-Based Score
    rule_score, rule_explanations = calculate_rule_based_score(text, url)
    
    # 2. Get ML-Based Score
    ml_score, ml_explanations = calculate_ml_score(text)
    
    # 3. Combine scores using predefined weights
    final_score = (rule_score * RULE_BASED_WEIGHT) + (ml_score * ML_BASED_WEIGHT)
    
    # --- Display Results ---
    print("\n" + "="*50)
    print("      CREDIBILITY ANALYSIS REPORT")
    print("="*50)
    
    print(f"\nFINAL CREDIBILITY SCORE: {final_score:.2f} / 100.00\n")
    
    print("-" * 20)
    print("Detailed Breakdown:")
    print("-" * 20)

    print("\n>>> Rule-Based Analysis (Weight: {:.0%})".format(RULE_BASED_WEIGHT))
    print(f"    Score: {rule_score:.2f}")
    for exp in rule_explanations:
        print(f"    - {exp}")
        
    print("\n>>> Linguistic Analysis (Weight: {:.0%})".format(ML_BASED_WEIGHT))
    print(f"    Score: {ml_score:.2f}")
    for exp in ml_explanations:
        print(f"    - {exp}")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    print("--- Credibility Score Analyzer (Proof of Concept) ---")
    user_input = input("Enter a URL or paste a block of text to analyze:\n> ")
    
    if user_input:
        analyze_credibility(user_input.strip())
