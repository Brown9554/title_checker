import os
import re
import sys

try:
    import shutil

    import undetected_chromedriver as uc
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:  # pragma: no cover - handled at runtime
    shutil = None
    uc = None
    Options = None
    Service = None
    TimeoutException = None
    By = None
    Keys = None
    EC = None
    WebDriverWait = None


def analyze_title_chain(address: str) -> str:
    """Placeholder function for title chain analysis."""
    return f"Title chain analysis for {address} is not implemented yet."


def normalize_street_name(street_name: str) -> str:
    street_name = street_name.strip()
    street_suffixes = [
        "street",
        "st",
        "road",
        "rd",
        "lane",
        "ln",
        "avenue",
        "ave",
        "boulevard",
        "blvd",
        "drive",
        "dr",
        "court",
        "ct",
        "place",
        "pl",
        "circle",
        "cir",
        "terrace",
        "ter",
        "trail",
        "trl",
        "parkway",
        "pkwy",
        "way",
        "wy",
        "close",
        "crescent",
        "crs",
    ]
    lowered = street_name.lower()
    for suffix in street_suffixes:
        if lowered.endswith(suffix):
            return street_name[: -len(suffix)].rstrip()
    return street_name


def parse_address_components(address: str):
    """Try to parse a full address into house number, street name, and town."""
    if not address or not address.strip():
        return None

    address = address.strip()

    if "," in address:
        parts = [part.strip() for part in address.split(",") if part.strip()]
        if len(parts) >= 3:
            return parts[0], normalize_street_name(parts[1]), parts[2]
        return None

    match = re.match(r"^(\d+)\s+(.+?)\s+([A-Za-z][A-Za-z .'-]+)$", address)
    if match:
        house_number = match.group(1)
        street_name = normalize_street_name(match.group(2))
        town = match.group(3).strip()
        if street_name and town:
            return house_number, street_name, town

    words = [word for word in re.split(r"\s+", address) if word]
    if len(words) >= 3 and re.match(r"^\d+", words[0]):
        return words[0], normalize_street_name(words[1]), words[-1]

    return None


def prompt_for_components():
    house_number = input("House number: ").strip()
    street_name = normalize_street_name(input("Street name (base name only): "))
    town = input("Town: ").strip()
    return house_number, street_name, town


def select_property_search(driver) -> bool:
    for select in driver.find_elements(By.TAG_NAME, "select"):
        try:
            options = select.find_elements(By.TAG_NAME, "option")
        except Exception:
            continue

        for option in options:
            if "property" in option.text.lower():
                try:
                    select.click()
                    option.click()
                    return True
                except Exception:
                    continue
    return False


def find_field(driver, keywords):
    for field in driver.find_elements(By.TAG_NAME, "input"):
        if not field.is_displayed():
            continue
        field_type = (field.get_attribute("type") or "").lower()
        if field_type in {"hidden", "submit", "button", "checkbox", "radio"}:
            continue

        attribute_text = " ".join(
            [
                field.get_attribute("id") or "",
                field.get_attribute("name") or "",
                field.get_attribute("placeholder") or "",
                field.get_attribute("aria-label") or "",
            ]
        ).lower()
        if any(keyword in attribute_text for keyword in keywords):
            return field
    return None


def fill_search_form(driver, house_number: str, street_name: str, town: str) -> None:
    select_property_search(driver)

    house_field = find_field(driver, ["house", "number", "houseno", "housenumber", "hnum"])
    if house_field is not None:
        house_field.clear()
        house_field.send_keys(house_number)

    street_field = find_field(driver, ["street", "streetname", "address", "roadname"])
    if street_field is not None:
        street_field.clear()
        street_field.send_keys(street_name)

    town_field = find_field(driver, ["town", "city", "municipality"])
    if town_field is not None:
        town_field.clear()
        town_field.send_keys(town)
        town_field.send_keys(Keys.RETURN)


def find_chromedriver_path():
    """Locate the system chromedriver binary automatically."""
    if shutil is None:
        return None

    candidates = []
    which_path = shutil.which("chromedriver")
    if which_path:
        candidates.append(which_path)

    common_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
        "/opt/chromedriver/chromedriver",
    ]
    for path in common_paths:
        if path not in candidates and os.path.exists(path):
            candidates.append(path)

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def find_browser_binary():
    """Locate a local Chrome/Chromium binary automatically."""
    if shutil is None:
        return None

    candidates = []
    for command in [
        "chromium-browser",
        "chromium",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
        "chrome-browser",
    ]:
        which_path = shutil.which(command)
        if which_path:
            candidates.append(which_path)

    common_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chrome",
        "/snap/bin/chromium",
    ]
    for path in common_paths:
        if path not in candidates and os.path.exists(path):
            candidates.append(path)

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def search_property(address: str) -> None:
    """Open the Mass Land Records site, search for an address, and print the result page details."""
    if uc is None or Options is None or Service is None or TimeoutException is None or By is None or Keys is None or EC is None or WebDriverWait is None:
        raise RuntimeError("undetected_chromedriver is required. Install it with 'pip install undetected-chromedriver'.")

    parsed_components = parse_address_components(address)
    if parsed_components is None:
        house_number, street_name, town = prompt_for_components()
    else:
        house_number, street_name, town = parsed_components

    chromedriver_path = find_chromedriver_path()
    if not chromedriver_path:
        raise RuntimeError("Could not find a chromedriver binary. Install it or make sure it is available on PATH.")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")

    browser_binary = find_browser_binary()
    if browser_binary:
        chrome_options.binary_location = browser_binary

    service = Service(executable_path=chromedriver_path)
    driver = uc.Chrome(options=chrome_options, version_main=149)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.masslandrecords.com")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        fill_search_form(driver, house_number, street_name, town)

        try:
            wait.until(
                lambda current_driver: "search" in current_driver.current_url.lower()
                or len(current_driver.find_elements(By.CSS_SELECTOR, "table, .result, .results")) > 0
            )
        except TimeoutException:
            pass

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        page_source = driver.page_source
        print(page_source[:2000])
        print(f"URL: {driver.current_url}")
    finally:
        driver.quit()


def main() -> None:
    address = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    try:
        search_property(address)
    except Exception as exc:
        print(f"Error during property search: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
