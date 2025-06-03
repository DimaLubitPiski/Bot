import requests
import time
import re

# Словарь сокращений
ADDRESS_ABBREVIATIONS = {
    r"\bул\b\.?": "улица",
    r"\bпр\b\.?": "проспект",
    r"\bпр-т\b\.?": "проспект",
    r"\bпл\b\.?": "площадь",
    r"\bпер\b\.?": "переулок",
    r"\bнаб\b\.?": "набережная",
    r"\bш\b\.?": "шоссе",
    r"\bбул\b\.?": "бульвар",
    r"\bд\b\.?": "дом",
    r"\bстр\b\.?": "строение",
    r"\bим\b\.?":"имени"
}


def normalize_address(address: str) -> str:
    """Заменяет сокращения в адресе на полные формы."""
    for pattern, replacement in ADDRESS_ABBREVIATIONS.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    return address


def get_district_from_address(address: str) -> str | None:
    """
    Получает район по адресу через OpenStreetMap Nominatim API.
    """
    normalized = normalize_address(address)

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{normalized}, Красноярск, Россия",
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
    }

    headers = {
        "User-Agent": "DPlaceFinder/1.0 (admin@gmail.com)"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()

        if not results:
            return None

        address_details = results[0].get("address", {})
        district = (
            address_details.get("city_district") or
            address_details.get("suburb") or
            address_details.get("neighbourhood")
        )
        return district
    except requests.RequestException as e:
        print("Ошибка при обращении к Nominatim:", e)
        return None
    finally:
        time.sleep(1)  # Вежливая пауза
