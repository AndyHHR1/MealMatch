import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os

SITES_TO_SCRAPE = [
    {
        "name": "RecetasGratis",
        "base_url": "https://www.recetasgratis.net",
        "search_url": "https://www.recetasgratis.net/recetas-peruanas",
        "allowed": True,
        "delay": 2,
    },
    {
        "name": "PeruCom",
        "base_url": "https://peru.com/recetas",
        "search_url": "https://peru.com/recetas/peruanas",
        "allowed": True,
        "delay": 2,
    },
]

HEADERS = {
    "User-Agent": "MealMatch-Bot/1.0 (proyecto-academico; contacto@mealmatch.pe)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}

def check_robots_txt(site):
    """Verifica robots.txt del sitio (básico)."""
    parsed = urlparse(site["base_url"])
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            print(f"[{site['name']}] robots.txt encontrado")
            return True
    except:
        pass
    return False

def scrape_recetasgratis(limit: int = 20) -> list:
    """Scrapea recetas peruanas de RecetasGratis.net"""
    recipes = []
    url = "https://www.recetasgratis.net/recetas-peruanas"
    
    try:
        print(f"[RecetasGratis] Scrapeando {url}...")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar enlaces a recetas
        recipe_links = []
        for link in soup.find_all('a', href=re.compile(r'/receta-peruana-')):
            href = link.get('href', '')
            if href.startswith('/'):
                href = urljoin(url, href)
            if href not in recipe_links:
                recipe_links.append(href)
        
        print(f"[RecetasGratis] Encontrados {len(recipe_links)} enlaces de recetas")
        
        # Scrapear cada receta (limitado)
        for recipe_url in recipe_links[:limit]:
            try:
                time.sleep(1.5)  # Respetar el servidor
                r = requests.get(recipe_url, headers=HEADERS, timeout=15)
                r.raise_for_status()
                recipe_soup = BeautifulSoup(r.text, 'html.parser')
                
                # Extraer título
                title = recipe_soup.find('h1')
                title = title.get_text(strip=True) if title else ""
                
                # Extraer ingredientes
                ingredients = []
                ingredients_section = recipe_soup.find('div', class_=re.compile('ingredientes|ingredients', re.I))
                if ingredients_section:
                    for li in ingredients_section.find_all('li'):
                        text = li.get_text(strip=True)
                        if text and len(text) > 2:
                            ingredients.append(text)
                
                # Extraer pasos
                steps = []
                steps_section = recipe_soup.find('div', class_=re.compile('preparacion|instructions|steps', re.I))
                if steps_section:
                    for p in steps_section.find_all(['p', 'li']):
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:
                            steps.append(text)
                
                if title and ingredients:
                    recipes.append({
                        "name": title,
                        "description": f"Receta peruana de {title.lower()}",
                        "ingredients": ingredients,
                        "steps": steps,
                        "source_url": recipe_url,
                        "source": "recetasgratis"
                    })
                    
            except Exception as e:
                print(f"[RecetasGratis] Error scrapeando {recipe_url}: {e}")
                continue
                
    except Exception as e:
        print(f"[RecetasGratis] Error general: {e}")
    
    return recipes


def scrape_peru_com(limit: int = 20) -> list:
    """Scrapea recetas peruanas de Peru.com"""
    recipes = []
    url = "https://peru.com/recetas/peruanas"
    
    try:
        print(f"[PeruCom] Scrapeando {url}...")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        recipe_links = []
        for link in soup.find_all('a', href=re.compile(r'/recetas?/')):
            href = link.get('href', '')
            if href.startswith('/'):
                href = urljoin(url, href)
            if href not in recipe_links:
                recipe_links.append(href)
        
        print(f"[PeruCom] Encontrados {len(recipe_links)} enlaces")
        
        for recipe_url in recipe_links[:limit]:
            try:
                time.sleep(1.5)
                r = requests.get(recipe_url, headers=HEADERS, timeout=15)
                r.raise_for_status()
                recipe_soup = BeautifulSoup(r.text, 'html.parser')
                
                title = recipe_soup.find('h1')
                title = title.get_text(strip=True) if title else ""
                
                ingredients = []
                ingredients_section = recipe_soup.find('ul', class_=re.compile('ingredientes|ingredients', re.I))
                if ingredients_section:
                    for li in ingredients_section.find_all('li'):
                        text = li.get_text(strip=True)
                        if text and len(text) > 2:
                            ingredients.append(text)
                
                steps = []
                steps_section = recipe_soup.find('ol', class_=re.compile('preparacion|instructions', re.I))
                if steps_section:
                    for li in steps_section.find_all('li'):
                        text = li.get_text(strip=True)
                        if text and len(text) > 10:
                            steps.append(text)
                
                if title and ingredients:
                    recipes.append({
                        "name": title,
                        "description": f"Receta peruana de {title.lower()}",
                        "ingredients": ingredients,
                        "steps": steps,
                        "source_url": recipe_url,
                        "source": "peru_com"
                    })
                    
            except Exception as e:
                print(f"[PeruCom] Error scrapeando {recipe_url}: {e}")
                continue
                
    except Exception as e:
        print(f"[PeruCom] Error general: {e}")
    
    return recipes


def scrape_all_recipes(max_per_site: int = 10) -> list:
    """Ejecuta scraping en todos los sitios configurados."""
    all_recipes = []
    
    for site in SITES_TO_SCRAPE:
        if not site["allowed"]:
            continue
            
        print(f"\n{'='*60}")
        print(f"Scrapeando {site['name']}...")
        print(f"{'='*60}")
        
        if site["name"] == "RecetasGratis":
            recipes = scrape_recetasgratis(limit=max_per_site)
        elif site["name"] == "PeruCom":
            recipes = scrape_peru_com(limit=max_per_site)
        else:
            recipes = []
        
        all_recipes.extend(recipes)
        print(f"✅ {site['name']}: +{len(recipes)} recetas")
    
    return all_recipes


if __name__ == "__main__":
    recipes = scrape_all_recipes(max_per_site=5)
    print(f"\n{'='*60}")
    print(f"Total recetas scrapeadas: {len(recipes)}")
    print(f"{'='*60}")
    
    if recipes:
        output_path = os.path.join(os.path.dirname(__file__), "..", "data", "scraped_recipes.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"recipes": recipes}, f, indent=2, ensure_ascii=False)
        print(f"✅ Guardado en: {output_path}")
