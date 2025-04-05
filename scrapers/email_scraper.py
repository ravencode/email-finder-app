import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

class EmailScraper:
    def __init__(self, timeout=10, sleep_between_requests=1):
        self.timeout = timeout
        self.sleep_between_requests = sleep_between_requests
        self.email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        self.contact_keywords = [
            "contact", "contactez", "contactez-nous", "kontakt", "contatti", "contacto",
            "联系我们", "聯絡我們", "联络我们", "お問い合わせ", "צור קשר", "सपर्क करें", "تماس با ما",
            "اتصل بنا", "연락처", "contact opnemen", "контакты", "контакти",
            "iletişim", "ติดต่อเรา", "liên hệ", "kontek"
        ]

    def format_url(self, url):
        if not url.startswith("http"):
            return "http://" + url
        return url

    def extract_emails_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        return set(self.email_regex.findall(text))

    def find_contact_links(self, soup, base_url):
        contact_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            text = link.get_text().lower()
            if any(k in href or k in text for k in self.contact_keywords):
                full_link = urljoin(base_url, link["href"])
                contact_links.append(full_link)
        return list(set(contact_links))

    def find_emails_from_site(self, site_url):
        logs = []
        found_emails = set()
        site_data = {
            "url": site_url,
            "emails": [],
            "logs": [],
            "status": "success"
        }

        try:
            response = requests.get(
                site_url, 
                timeout=self.timeout, 
                headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Homepage emails
            homepage_emails = self.extract_emails_from_html(response.text)
            found_emails.update(homepage_emails)
            logs.append(f"✅ {site_url}: {len(homepage_emails)} email(s) from homepage")

            # Contact-like links
            contact_links = self.find_contact_links(soup, site_url)
            logs.append(f"🔎 {site_url}: Found {len(contact_links)} possible contact page(s)")

            # Crawl contact pages
            for contact_url in contact_links:
                try:
                    res = requests.get(
                        contact_url, 
                        timeout=self.timeout, 
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    res.raise_for_status()
                    page_emails = self.extract_emails_from_html(res.text)
                    found_emails.update(page_emails)
                    logs.append(f"📄 {contact_url}: {len(page_emails)} email(s)")
                    time.sleep(self.sleep_between_requests)
                except Exception as e:
                    logs.append(f"⚠️ Could not access {contact_url}: {str(e)}")

        except Exception as e:
            logs.append(f"❌ {site_url}: Failed to load - {str(e)}")
            site_data["status"] = "error"
        
        site_data["emails"] = list(found_emails)
        site_data["logs"] = logs
        return site_data