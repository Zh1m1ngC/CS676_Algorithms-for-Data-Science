# credibility_analyzer.py

import re
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from urllib.parse import urlparse
import trafilatura

# --- Configuration ---
CONFIG = {
    'weights': { 'rule_based': 0.4, 'ml_based': 0.6, },
    'domains': {
        'high_credibility': ['reuters.com', 'apnews.com', 'bbc.com', 'npr.org', 'pbs.org', 'nytimes.com', 'wsj.com', 'washingtonpost.com', 'theguardian.com', 'propublica.org', 'theatlantic.com', 'economist.com', '.gov', '.edu', 'nature.com', 'sciencemag.org', 'thelancet.com', 'cell.com', 'arxiv.org', 'jstor.org', 'pubmed.ncbi.nlm.nih.gov'],
        'medium_credibility': ['forbes.com', 'huffpost.com', 'buzzfeednews.com', 'theverge.com', 'vox.com', 'slate.com', 'vice.com', 'salon.com', 'msnbc.com', 'foxnews.com', 'nypost.com'],
        'low_credibility': ['infowars.com', 'breitbart.com', 'dailycaller.com', 'thegatewaypundit.com', 'naturalnews.com', 'wnd.com', 'theblaze.com', 'dailywire.com', 'theonion.com', 'babylonbee.com', 'worldnewsdailyreport.com']
    }, 'word_count_threshold': 250
}

def calculate_rule_based_score(text, url=None, title=None):
    score = 50
    explanations = []
    if url:
        domain = urlparse(url).netloc.replace('www.', '')
        domain_found = False
        for high_cred_domain in CONFIG['domains']['high_credibility']:
            if domain.endswith(high_cred_domain):
                score += 30; explanations.append(f"[+30] **Source Reputation**: Domain '{domain}' is highly credible."); domain_found = True; break
        if not domain_found:
            for med_cred_domain in CONFIG['domains']['medium_credibility']:
                if domain.endswith(med_cred_domain):
                    score += 5; explanations.append(f"[+5] **Source Reputation**: Domain '{domain}' is moderately credible."); domain_found = True; break
        if not domain_found:
            for low_cred_domain in CONFIG['domains']['low_credibility']:
                if domain.endswith(low_cred_domain):
                    score -= 35; explanations.append(f"[-35] **Source Reputation**: Domain '{domain}' has low credibility."); domain_found = True; break
        if not domain_found:
            explanations.append("[+/- 0] **Source Reputation**: Domain is not on predefined lists.")
    if re.search(r'\b(by|author)\s+([A-Z][a-z]+(\s+[A-Z][a-z]+)+)', text[:500], re.IGNORECASE):
        score += 10; explanations.append("[+10] **Author Presence**: An author byline was found.")
    else:
        score -= 5; explanations.append("[-5] **Author Presence**: No clear author byline detected.")
    if re.search(r'\b(sources|references|citations|bibliography)\b', text, re.IGNORECASE):
        score += 15; explanations.append("[+15] **Citations**: The article appears to cite sources.")
    else:
        explanations.append("[+/- 0] **Citations**: No dedicated sources section found.")
    num_all_caps = len(re.findall(r'\b[A-Z]{4,}\b', text)); num_exclamations = text.count('!')
    if num_all_caps > 5 or num_exclamations > 5:
        penalty = min((num_all_caps + num_exclamations - 10) * 2, 20); score -= penalty
        explanations.append(f"[-{penalty}] **Sensationalism**: Excessive use of ALL CAPS or '!' detected.")
    else:
        explanations.append("[+/- 0] **Sensationalism**: Language appears temperate.")
    if title:
        clickbait_patterns = [r'\b(will blow your mind|you won\'t believe|shocking|secret|what happens next)\b', r'\?$', r'^\d+\s+(reasons|tips|tricks|ways)\s+']
        if any(re.search(p, title, re.IGNORECASE) for p in clickbait_patterns):
            score -= 15; explanations.append("[-15] **Headline Analysis**: The title appears to be clickbait.")
        else:
            explanations.append("[+/- 0] **Headline Analysis**: Title seems straightforward.")
    word_count = len(text.split())
    if word_count < CONFIG['word_count_threshold']:
        score -= 10; explanations.append(f"[-10] **Article Depth**: The article is very short ({word_count} words).")
    else:
        explanations.append(f"[+/- 0] **Article Depth**: Article has sufficient length ({word_count} words).")
    return max(0, min(100, score)), explanations

def calculate_ml_score(text):
    if not text or not text.strip(): return 0, ["[-100] **Text Content**: No text could be extracted."]
    blob = TextBlob(text); explanations = []
    subjectivity = blob.sentiment.subjectivity; subjectivity_score = (1 - subjectivity) * 100
    if subjectivity > 0.6: explanation = f"High Subjectivity ({subjectivity:.2f}). The text seems heavily opinion-based."
    elif subjectivity < 0.3: explanation = f"High Objectivity ({subjectivity:.2f}). The text appears to be fact-based."
    else: explanation = f"Moderate Subjectivity ({subjectivity:.2f}). A mix of facts and opinion."
    explanations.append(f"**Linguistic Analysis**: {explanation}")
    polarity = abs(blob.sentiment.polarity); polarity_score = (1 - polarity) * 100
    if polarity > 0.5: explanation = f"Strong Sentiment ({blob.sentiment.polarity:.2f}). Language is highly emotional."
    else: explanation = f"Neutral Sentiment ({blob.sentiment.polarity:.2f}). The tone is relatively neutral."
    explanations.append(f"**Sentiment Analysis**: {explanation}")
    return max(0, min(100, (subjectivity_score + polarity_score) / 2)), explanations

def get_content_from_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded: return None, None
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        soup = BeautifulSoup(downloaded, 'html.parser')
        title = soup.find('title').string if soup.find('title') else "No Title Found"
        return text, title
    except Exception as e:
        print(f"Error extracting content: {e}"); return None, None

def analyze_credibility(user_input):
    text, url, title = "", None, ""
    if user_input.startswith(('http://', 'https://')):
        url = user_input
        text, title = get_content_from_url(url)
        if not text: return "❌ **Error**: Could not retrieve content from the URL."
    else:
        text = user_input
    if len(text.split()) < 50: return "⚠️ **Warning**: Input is too short for a meaningful credibility analysis."
    rule_score, rule_explanations = calculate_rule_based_score(text, url, title)
    ml_score, ml_explanations = calculate_ml_score(text)
    final_score = (rule_score * CONFIG['weights']['rule_based']) + (ml_score * CONFIG['weights']['ml_based'])
    report_lines = [
        "##  Credibility Analysis Report", f"### **Final Credibility Score: `{final_score:.2f} / 100.00`**", "---",
        "#### Detailed Breakdown:", f"##### Rule-Based Analysis (Weight: {CONFIG['weights']['rule_based']:.0%})", f"* **Score:** `{rule_score:.2f}`"
    ] + [f"* {exp}" for exp in rule_explanations] + [
        f"\n##### Linguistic Analysis (Weight: {CONFIG['weights']['ml_based']:.0%})", f"* **Score:** `{ml_score:.2f}`"
    ] + [f"* {exp}" for exp in ml_explanations]
    return "\n".join(report_lines)