import requests
from bs4 import BeautifulSoup
import re



'''
The below is for the scraping for ai
'''

blacklist_phrases = [
    "cookie policy",
    "privacy policy",
    "use of cookies",
    "cookie settings",
    "terms of use",
    "legal notice",
    "data protection",
    "your privacy choices",
    "gdpr compliance",
    "ccpa compliance",
    "do not sell my personal information",
    "advertising preferences",
    "tracking technologies",
    "information collection",
    "data security",
    "consent management",
    "browser cookies",
    "third-party cookies",
    "essential cookies",
    "performance cookies",
    "analytics cookies",
    "functional cookies",
    "targeting cookies",
    "advertising cookies",
    "opt-out of cookies",
    "your browser settings",
    "storage and access of cookies",
    "our commitment to privacy",
    "how we use your data",
    "your rights",
    "changes to this policy",
    "contact us regarding privacy",
    "effective date of policy",
    "last updated privacy",
    "personal data collected",
    "user data collection",
    "aggregate data usage",
    "log files and privacy",
    "ip address logging policy",
    "device information privacy",
    "web beacons and privacy",
    "pixel tags and data",
    "local storage and cookies",
    "session storage and user data",
    "security measures for data",
    "data retention policy",
    "international data transfers",
    "children's privacy policy",
    "manage your preferences",
    "about our ads",
    "ad choices",
    "your ad preferences",
    "learn more about cookies",
    "manage tracking preferences",
    "your data rights",
    "site terms and conditions",
    "copyright policy",
    "trademark policy",
    "accessibility statement",
    "feedback policy",
    "report a problem",
    "help center",
    "support center",
    "contact support",
    "site map",
    "about us",
    "careers",
    "press releases",
    "investor relations",
    "subscribe to our newsletter",
    "download our app"
]

def scrape_article_p_tags(url):
    """
    Scrapes the text content of an article, focusing on <p> tags,
    cleans up the text, removes privacy/cookie statements, and limits to 1500 words.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

       

        # Remove footer and other cookie-related elements
        for tag in soup.find_all(['footer', 'aside', 'nav']):
            tag.decompose()

        for div in soup.find_all('div', class_=re.compile(r'(cookie|privacy|legal)', re.IGNORECASE)):
            div.decompose()

        # Remove <p> tags with class containing "cookie"
        for p in soup.find_all('p', class_=re.compile(r'cookie', re.IGNORECASE)):
            p.decompose()

        paragraphs = soup.find_all("p")
        #print(paragraphs)
        article_text = ""
        word_count = 0

        for p in paragraphs:

            text = p.get_text(strip=True).lower()
            if any(phrase in text for phrase in blacklist_phrases):
                continue
            text = p.get_text(strip=True)

            # Clean up the text:
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[\r\n]+', '\n', text)
            text = text.strip()

            if text:
                words = text.split()
                if word_count + len(words) <= 1500:
                    article_text += text + "\n"
                    word_count += len(words)
                else:
                    break

        if not article_text.strip():
            print(f"Warning: No article text found at {url} within <p> tags.")
            return None

        # Remove privacy/cookie statements using regex
        #article_text = remove_privacy_statements(article_text)

        # Truncate to 1500 words after regex cleanup (if necessary)
        words = article_text.split()
        if len(words) > 1500:
            article_text = " ".join(words[:1500])

        return article_text

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def remove_privacy_statements(text):
    """Removes common privacy and cookie statements from the text."""
    patterns = [
        r"Privacy Policy.*",
        r"Cookie Policy.*",
        r"This site uses cookies.*",
        r"Legal Disclaimer.*",
        r"Terms of Use.*",
        r"©.*(All Rights Reserved|Copyright).*",
        r"We use cookies to.*",
        r"By using this site, you agree to our use of cookies.*",
        r"Manage Cookie Preferences.*",
        r"Accept Cookies.*",
        r"Reject Cookies.*",
        r"Cookie Settings.*",
        r"use cookies.*",
        r"Data Protection.*",
        r"Your Privacy Choices.*",
        r"GDPR.*",
        r"CCPA.*",
        r"Do Not Sell My Personal Information.*",
        r"Advertising Preferences.*",
        r"Tracking Technologies.*",
        r"Information Collection.*",
        r"Data Security.*",
        r"Consent Management.*",
        r"Browser Cookies.*",
        r"Third-Party Cookies.*",
        r"Essential Cookies.*",
        r"Performance Cookies.*",
        r"Analytics Cookies.*",
        r"Functional Cookies.*",
        r"Targeting Cookies.*",
        r"Advertising Cookies.*",
        r"Opt-out of cookies.*",
        r"Your browser settings.*",
        r"Storage and Access of Cookies.*",
        r"Our commitment to privacy.*",
        r"How we use your data.*",
        r"Your rights.*",
        r"Changes to this policy.*",
        r"Contact us.*",
        r"Effective Date.*",
        r"Last Updated.*",
        r"Personal Data.*",
        r"User Data.*",
        r"Aggregate Data.*",
        r"Log Files.*",
        r"IP Address.*",
        r"Device Information.*",
        r"Web Beacons.*",
        r"Pixel Tags.*",
        r"Local Storage.*",
        r"Session Storage.*",
        r"Security Measures.*",
        r"Data Retention.*",
        r"International Data Transfers.*",
        r"Children's Privacy.*",
        r"Reddit and its partners use cookies.*Cookie Notice.*Privacy Policy.*"
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    return text
