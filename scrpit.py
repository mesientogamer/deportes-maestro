import requests

SOURCE_URL = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT_FILE = "parrilla_deportes_automatica.m3u"

# Idiomas permitidos.
# Esto es un filtro de idioma, no un mecanismo para eludir
# restricciones geográficas o de emisión.
ALLOWED_LANGUAGES = {
    "ara",
    "rus",
    "tur",
    "fas",
    "per",
}

SPORT_ORDER = [
    ("Motor", {"motor", "motorsport", "formula 1", "formula1", "f1"}),
    ("Fútbol", {"football", "soccer", "futbol"}),
    ("Tenis", {"tennis"}),
    ("Baloncesto", {"basketball"}),
    ("MMA", {"mma", "ufc", "mixed martial arts"}),
    ("Balonmano", {"handball"}),
]


def download_playlist():
    response = requests.get(
        SOURCE_URL,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def parse_m3u(text):
    channels = []
    current_info = None

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current_info = line

        elif current_info and not line.startswith("#"):
            channels.append((current_info, line))
            current_info = None

    return channels


def get_attribute(extinf, attribute):
    prefix = f'{attribute}="'

    start = extinf.find(prefix)

    if start == -1:
        return ""

    start += len(prefix)
    end = extinf.find('"', start)

    if end == -1:
        return ""

    return extinf[start:end]


def channel_name(extinf):
    if "," in extinf:
        return extinf.rsplit(",", 1)[1].strip()

    return extinf.strip()


def normalize(value):
    return value.lower().strip()


def language_allowed(extinf):
    language = get_attribute(extinf, "tvg-language")

    if not language:
        return False

    languages = {
        normalize(item)
        for item in language.replace(";", ",").split(",")
        if item.strip()
    }

    return bool(languages & ALLOWED_LANGUAGES)


def detect_sport(extinf):
    text = normalize(extinf)

    for sport, keywords in SPORT_ORDER:
        for keyword in keywords:
            if keyword in text:
                return sport

    return None


def build_playlist(channels):
    grouped = {sport: [] for sport, _ in SPORT_ORDER}

    for extinf, url in channels:
        if not language_allowed(extinf):
            continue

        sport = detect_sport(extinf)

        if sport is None:
            continue

        grouped[sport].append((extinf, url))

    output = ["#EXTM3U"]

    for sport, _ in SPORT_ORDER:
        output.append("")
        output.append(f"# ===== {sport} =====")

        for extinf, url in grouped[sport]:
            output.append(extinf)
            output.append(url)

    return "\n".join(output) + "\n"


def main():
    print("Descargando lista IPTV...")
    playlist = download_playlist()

    print("Analizando canales...")
    channels = parse_m3u(playlist)

    print(f"Canales encontrados: {len(channels)}")

    result = build_playlist(channels)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        file.write(result)

    print(f"Archivo generado: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
