import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote
from playwright.sync_api import sync_playwright

DEPT_URL = "https://www.sante.fr/categories/chirurgie-dentaire/16-charente"
BASE_SEARCH = "https://www.sante.fr/recherche/trouver/Chirurgie%20dentaire/"
COLUMNS = ["Nom", "Rue", "Code_postal", "Ville", "Telephone"]


def clean_text(x: str) -> str:
    if not x:
        return ""
    return re.sub(r"\s+", " ", x).strip()


def normalize_phone(s: str) -> str:
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    if digits.startswith("33"):
        digits = "0" + digits[2:]
    if len(digits) == 10:
        return f"{digits[0:2]} {digits[2:4]} {digits[4:6]} {digits[6:8]} {digits[8:10]}"
    return clean_text(s)


def split_address(addr: str):
    addr = clean_text(addr)
    if not addr:
        return "", "", ""
    m = re.search(r"^(.*?)[,\s]+(\d{5})\s+(.+)$", addr)
    if m:
        return clean_text(m.group(1)).rstrip(",;"), m.group(2), clean_text(m.group(3))
    return addr, "", ""


def accept_cookies_if_present(page):
    for sel in [
        "button:has-text('Tout accepter')",
        "button:has-text('Accepter')",
        "button:has-text('J’accepte')",
        "button:has-text(\"J'accepte\")",
        "button:has-text('OK')",
    ]:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=1500)
                page.wait_for_timeout(500)
                return
            except Exception:
                pass


def get_city_strings_via_playwright(page):
    page.goto(DEPT_URL, wait_until="networkidle")
    page.wait_for_timeout(1500)
    accept_cookies_if_present(page)

    # scroll pour charger au max
    for _ in range(10):
        page.mouse.wheel(0, 1600)
        page.wait_for_timeout(500)

    html = page.content()

    # Debug si ça foire
    if "charente" not in html.lower():
        page.screenshot(path="debug_dept.png", full_page=True)
        with open("debug_dept.html", "w", encoding="utf-8") as f:
            f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    city_strings = set()
    for line in text.split("\n"):
        line = clean_text(line)
        # "16000 Angoulême"
        if re.match(r"^\d{5}\s+.+", line) and len(line) <= 80:
            city_strings.add(line)

    return sorted(city_strings)


def build_search_url(city_string: str) -> str:
    return BASE_SEARCH + quote(city_string)


def extract_results_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    chunks = text.split("Adresse")
    rows = []

    for c in chunks[1:]:
        block = clean_text("Adresse " + c)

        # Nom
        name = ""
        m_name = re.search(r"\b(Dr\s+[A-Za-zÀ-ÿ'\-\s]{2,60})\b", block)
        if m_name:
            name = clean_text(m_name.group(1))
        else:
            m_name2 = re.search(r"\b(Centre dentaire[^\n]{0,80})\b", block, flags=re.IGNORECASE)
            if m_name2:
                name = clean_text(m_name2.group(1))

        # Adresse
        addr = ""
        m_addr = re.search(r"Adresse\s*:?(.+?\b\d{5}\b\s+[A-Za-zÀ-ÿ\-\s']+)", block)
        if m_addr:
            addr = clean_text(m_addr.group(1))

        # Téléphone
        phone = ""
        m_phone = re.search(r"Téléphone\s*:?\s*([0-9\s\.\-\+]{8,})", block)
        if m_phone:
            phone = normalize_phone(m_phone.group(1))

        street, cp, city = split_address(addr)

        if name or addr or phone:
            rows.append({
                "Nom": name,
                "Rue": street,
                "Code_postal": cp,
                "Ville": city,
                "Telephone": phone
            })

    return [r for r in rows if any(r[k] for k in r)]


def main():
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cities = get_city_strings_via_playwright(page)
        print(f"✅ Villes détectées via Playwright: {len(cities)}")

        if len(cities) == 0:
            print("❌ Toujours 0 ville. Regarde debug_dept.png et debug_dept.html (créés si besoin).")
            browser.close()
            return

        search_urls = [build_search_url(c) for c in cities]

        for i, url in enumerate(search_urls, start=1):
            print(f"[{i}/{len(search_urls)}] {url}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1800)
            accept_cookies_if_present(page)

            # scroll pour charger résultats
            for _ in range(6):
                page.mouse.wheel(0, 1600)
                page.wait_for_timeout(600)

            html = page.content()
            all_rows.extend(extract_results_from_html(html))
            time.sleep(0.15)

        browser.close()

    df = pd.DataFrame(all_rows, columns=COLUMNS)

    for col in COLUMNS:
        df[col] = df[col].fillna("").map(clean_text)

    df = df.drop_duplicates()
    df = df[(df["Nom"] != "") | (df["Rue"] != "") | (df["Telephone"] != "")]

    df.to_excel("dentistes_charente_16.xlsx", index=False)
    df.to_csv("dentistes_charente_16.csv", index=False, encoding="utf-8-sig")

    print("\n✅ Terminé")
    print("📄 dentistes_charente_16.xlsx")
    print("📄 dentistes_charente_16.csv")
    print(f"🧾 Lignes extraites: {len(df)}")


if __name__ == "__main__":
    main()
