import requests
from bs4 import BeautifulSoup

def find_linkedin_people(company_name, role="HR"):
    query = f'site:linkedin.com/in "{role}" "{company_name}"'
    url = f"https://www.google.com/search?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for g in soup.find_all('div', class_='tF2Cxc')[:5]:
        link = g.find('a')['href']
        title = g.find('h3').text
        results.append({
            "name_role": title,
            "linkedin_url": link
        })

    return results