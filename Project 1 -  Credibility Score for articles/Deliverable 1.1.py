import re
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from urllib.parse import urlparse
import trafilatura

# --- Configuration ---

CONFIG = {
    'weights': {
        'rule_based': 0.4, # Reduced weight to decrease reliance on predefined lists
        'ml_based': 0.6,
    },
    'domains': {
        'high_credibility': [
            # News & Journalism
            'reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'pbs.org',
            'nytimes.com', 'wsj.com', 'washingtonpost.com', 'theguardian.com',
            'propublica.org', 'theatlantic.com', 'economist.com',
            # Academic & Scientific
            '.gov', '.edu', 'nature.com', 'sciencemag.org', 'thelancet.com',
            'cell.com', 'arxiv.org', 'jstor.org', 'pubmed.ncbi.nlm.nih.gov'
        ],
        'medium_credibility': [
            # Often have partisan slants or focus on opinion
            'forbes.com', 'huffpost.com', 'buzzfeednews.com', 'theverge.com',
            'vox.com', 'slate.com', 'vice.com', 'salon.com', 'msnbc.com',
            'foxnews.com', 'nypost.com'
        ],
        'low_credibility': [
            # Known for misinformation, conspiracy, or extreme bias
            'infowars.com', 'breitbart.com', 'dailycaller.com', 'thegatewaypundit.com',
            'naturalnews.com', 'wnd.com', 'theblaze.com', 'dailywire.com',
            # Satire sites (often mistaken for news)
            'theonion.com', 'babylonbee.com', 'worldnewsdailyreport.com'
        ]
    },
    'word_count_threshold': 250
}

# --- Component 1: Rule-Based Engine ---

def calculate_rule_based_score(text, url=None, title=None):
    """Calculates a credibility score based on a set of predefined rules."""
    score = 50  # Start with a neutral score
    explanations = []

    # Rule 1: Source Reputation (from URL)
    if url:
        domain = urlparse(url).netloc.replace('www.', '')
        domain_found = False
        # Check high credibility
        for high_cred_domain in CONFIG['domains']['high_credibility']:
            if domain.endswith(high_cred_domain):
                score += 30
                explanations.append(f"[+30] Source Reputation: Domain '{domain}' is highly credible.")
                domain_found = True
                break
        # Check medium credibility
        if not domain_found:
            for med_cred_domain in CONFIG['domains']['medium_credibility']:
                if domain.endswith(med_cred_domain):
                    score += 5
                    explanations.append(f"[+5] Source Reputation: Domain '{domain}' is moderately credible (often opinionated).")
                    domain_found = True
                    break
        # Check low credibility
        if not domain_found:
            for low_cred_domain in CONFIG['domains']['low_credibility']:
                if domain.endswith(low_cred_domain):
                    score -= 35
                    explanations.append(f"[-35] Source Reputation: Domain '{domain}' has low credibility.")
                    domain_found = True
                    break
        if not domain_found:
            explanations.append("[+/- 0] Source Reputation: Domain is not on predefined lists.")

    # Rule 2: Presence of Author
    if re.search(r'\b(by|author)\s+([A-Z][a-z]+(\s+[A-Z][a-z]+)+)', text[:500], re.IGNORECASE):
        score += 10
        explanations.append("[+10] Author Presence: An author byline was found.")
    else:
        score -= 5
        explanations.append("[-5] Author Presence: No clear author byline detected.")

    # Rule 3: Presence of Citations/Sources
    if re.search(r'\b(sources|references|citations|bibliography)\b', text, re.IGNORECASE):
        score += 15
        explanations.append("[+15] Citations: The article appears to cite sources.")
    else:
        explanations.append("[+/- 0] Citations: No dedicated sources section found.")

    # Rule 4: Sensationalism (excessive caps or exclamation points)
    num_all_caps = len(re.findall(r'\b[A-Z]{4,}\b', text))
    num_exclamations = text.count('!')
    if num_all_caps > 5 or num_exclamations > 5:
        penalty = min((num_all_caps + num_exclamations - 10) * 2, 20)
        score -= penalty
        explanations.append(f"[-{penalty}] Sensationalism: Excessive use of ALL CAPS or '!' detected.")
    else:
        explanations.append("[+/- 0] Sensationalism: Language appears temperate.")

    # Rule 5: Clickbait Headline Detection
    if title:
        clickbait_patterns = [
            r'\b(will blow your mind|you won\'t believe|shocking|secret|what happens next)\b',
            r'\?$', # Ends with a question mark
            r'^\d+\s+(reasons|tips|tricks|ways)\s+' # Starts with "10 reasons..."
        ]
        is_clickbait = any(re.search(p, title, re.IGNORECASE) for p in clickbait_patterns)
        if is_clickbait:
            score -= 15
            explanations.append("[-15] Headline Analysis: The title appears to be clickbait.")
        else:
            explanations.append("[+/- 0] Headline Analysis: Title seems straightforward.")

    # Rule 6: Word Count
    word_count = len(text.split())
    if word_count < CONFIG['word_count_threshold']:
        score -= 10
        explanations.append(f"[-10] Article Depth: The article is very short ({word_count} words), suggesting a lack of depth.")
    else:
        explanations.append(f"[+/- 0] Article Depth: Article has sufficient length ({word_count} words).")


    final_score = max(0, min(100, score))
    return final_score, explanations

# --- Component 2: ML-Based Engine (Simulated with TextBlob) ---

def calculate_ml_score(text):
    """Analyzes text for linguistic cues of credibility using TextBlob."""
    if not text or not text.strip():
        return 0, ["[-100] Text Content: No text was provided or could be extracted."]

    blob = TextBlob(text)
    explanations = []

    # Metric 1: Subjectivity (0.0=objective, 1.0=subjective)
    subjectivity = blob.sentiment.subjectivity
    subjectivity_score = (1 - subjectivity) * 100
    if subjectivity > 0.6:
        explanation = f"High Subjectivity ({subjectivity:.2f}). The text seems heavily opinion-based."
    elif subjectivity < 0.3:
        explanation = f"High Objectivity ({subjectivity:.2f}). The text appears to be fact-based."
    else:
        explanation = f"Moderate Subjectivity ({subjectivity:.2f}). A mix of facts and opinion."
    explanations.append(f"Analysis: {explanation}")

    # Metric 2: Polarity (measures sentiment, -1.0 to 1.0)
    polarity = abs(blob.sentiment.polarity)
    polarity_score = (1 - polarity) * 100
    if polarity > 0.5:
        explanation = f"Strong Sentiment ({blob.sentiment.polarity:.2f}). The language is highly emotional, which may indicate bias."
    else:
        explanation = f"Neutral Sentiment ({blob.sentiment.polarity:.2f}). The tone is relatively neutral."
    explanations.append(f"Analysis: {explanation}")

    final_score = (subjectivity_score + polarity_score) / 2
    return max(0, min(100, final_score)), explanations

# --- Utility Functions ---

def get_content_from_url(url):
    """
    Fetches and extracts the main text content and title from a URL.
    Uses trafilatura for robust extraction.
    """
    try:
        # Fetch the webpage
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print("Failed to download the URL content.")
            return None, None

        # Extract main text content
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)

        # Extract title using BeautifulSoup as a fallback
        soup = BeautifulSoup(downloaded, 'html.parser')
        title = soup.find('title').string if soup.find('title') else "No Title Found"

        return text, title
    except Exception as e:
        print(f"An error occurred during extraction: {e}")
        return None, None

# --- Main Controller ---

def analyze_credibility(user_input):
    """Main function to analyze input (URL or text) and return a credibility score."""
    text, url, title = "", None, None

    if user_input.startswith(('http://', 'https://')):
        url = user_input
        print("Fetching and parsing article from URL...")
        text, title = get_content_from_url(url)
        if not text:
            print("Could not retrieve meaningful content from the URL.")
            return
    else:
        text = user_input
        if len(text.split()) > 40: # If it's a long text, no title
             title = "User-provided text"
        else: # If it's short, treat it as a headline
            title = text

    if len(text.split()) < 50 and url is None:
        print("Input text is too short for a meaningful analysis. Please provide more text or a URL.")
        return

    rule_score, rule_explanations = calculate_rule_based_score(text, url, title)
    ml_score, ml_explanations = calculate_ml_score(text)

    # Combine scores using configured weights
    final_score = (rule_score * CONFIG['weights']['rule_based']) + \
                  (ml_score * CONFIG['weights']['ml_based'])

    # --- Display Results ---
    print("\n" + "="*50)
    print("      CREDIBILITY ANALYSIS REPORT")
    print("="*50)

    print(f"\nFINAL CREDIBILITY SCORE: {final_score:.2f} / 100.00\n")

    print("-" * 20)
    print("Detailed Breakdown:")
    print("-" * 20)

    print("\n>>> Rule-Based Analysis (Weight: {:.0%})".format(CONFIG['weights']['rule_based']))
    print(f"    Score: {rule_score:.2f}")
    for exp in rule_explanations:
        print(f"    - {exp}")

    print("\n>>> Linguistic Analysis (Weight: {:.0%})".format(CONFIG['weights']['ml_based']))
    print(f"    Score: {ml_score:.2f}")
    for exp in ml_explanations:
        print(f"    - {exp}")

    print("\n" + "="*50)


if __name__ == "__main__":
    print("--- Credibility Score Analyzer v2.0 ---")
    user_input = input("Enter a URL or paste a block of text to analyze:\n> ")

    if user_input:
        analyze_credibility(user_input.strip())