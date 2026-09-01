import requests
import re

OUTPUT_FILE = "parrilla_deportes_automatica.m3u"

# Fuentes públicas de IPTV-org agrupadas por idioma.
LANGUAGE_PLAYLISTS = {
    "Árabe": "https://iptv-org.github.io/iptv/languages/ara.m3u",
    "Persa": "https://iptv-org.github.io/iptv/languages/fas.m3u",
    "Ruso": "https://iptv-org.github.io/iptv/languages/rus.m3u",
    "Turco": "https://iptv-org.github.io/iptv/languages/tur.m3u",
    "Urdu": "https://iptv-org.github.io/iptv/languages/urd.m3u",
    "Vietnamita": "https://iptv-org.github.io/iptv/languages/vie.m3u",
    "Ucraniano": "https://iptv-org.github.io/iptv/languages/ukr.m3u",
    "Uzbeko": "https://iptv-org.github.io/iptv/languages/uzb.m3u",
    "Kazajo": "https://iptv-org.github.io/iptv/languages/kaz.m3u",
    "Kurdo": "https://iptv-org.github.io/iptv/languages/kur.m3u",
    "Azerí": "https://iptv-org.github.io/iptv/languages/aze.m3u",
    "Georgiano": "https://iptv-org.github.io/iptv/languages/kat.m3u",
    "Armenio": "https://iptv-org.github.io/iptv/languages/hye.m3u",
}

# Orden estricto de la parrilla.
SPORTS = [
    (
        "1. FÚTBOL",
        [
            "football", "soccer", "futbol", "fútbol",
            "bein", "ssc", "alkass", "laliga",
            "champions", "premier league"
        ],
    ),
    (
        "2. TENIS",
        [
            "tennis", "tenis", "atp", "wta",
            "wimbledon", "roland garros",
            "us open", "australian open"
        ],
    ),
    (
        "3. BALONCESTO",
        [
            "basketball", "baloncesto", "nba",
            "euroleague", "eurocup", "acb"
        ],
    ),
    (
        "4. MMA",
        [
            "mma", "ufc", "mixed martial arts",
            "boxing", "boxeo", "fight"
        ],
    ),
    (
        "5. BALONMANO",
        [
            "handball", "balonmano""handball","balonmano", "handbol", "handboll", "handbold", "hentbol", "гандбол", "гандболь",
        ],
    ),
    (
        "6. MOTOR",
        [
            "formula 1", "formula1", "f1",
            "motogp", "moto gp", "motorsport",
            "racing", "motor"
        ],
    ),
]


def normalize(text):
    return text.lower().strip()


def get_attribute(metadata, attribute):
    pattern = rf'{re.escape(attribute)}="([^"]*)"'
    match = re.search(pattern, metadata, re.IGNORECASE)

    if match:
        return match.group(1)

    return ""


def get_channel_name(metadata):
    # No usamos split(",") para analizar toda la línea.
    position = metadata.rfind(",")

    if position >= 0:
        return metadata[position + 1:].strip()

    return "Canal deportivo"


def detect_sport(metadata):
    text = normalize(metadata)

    for sport, keywords in SPORTS:
        for keyword in keywords:
            if keyword in text:
                return sport

    return None


def parse_m3u(text):
    channels = []
    metadata = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            metadata = line
            continue

        if metadata and line.startswith(("http://", "https://")):
            channels.append((metadata, line))
            metadata = None

    return channels


def download_language_playlist(language, url):
    print(f"Descargando {language}...")

    response = requests.get(
        url,
        timeout=60,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    response.raise_for_status()
    response.encoding = "utf-8"

    return response.text


def main():
    all_channels = []
    seen_urls = set()

    # Descargar todas las listas de idiomas.
    for language, url in LANGUAGE_PLAYLISTS.items():

        try:
            text = download_language_playlist(language, url)
            channels = parse_m3u(text)

            print(
                f" {language}: "
                f"{len(channels)} canales encontrados"
            )

            for metadata, stream_url in channels:

                # Evitar duplicados.
                if stream_url in seen_urls:
                    continue

                seen_urls.add(stream_url)

                all_channels.append(
                    (language, metadata, stream_url)
                )

        except requests.RequestException as error:
            print(
                f" ERROR descargando {language}: {error}"
            )

    print()
    print(
        f"Total de canales únicos: "
        f"{len(all_channels)}"
    )

    # Agrupar por deporte.
    grouped = {
        sport: []
        for sport, _ in SPORTS
    }

    for language, metadata, stream_url in all_channels:

        sport = detect_sport(metadata)

        if sport is None:
            continue

        grouped[sport].append(
            (
                language,
                metadata,
                stream_url
            )
        )

    # Crear M3U.
    output = ["#EXTM3U"]

    total = 0

    for sport, _ in SPORTS:

        output.append("")
        output.append(
            f"# ===== {sport} ====="
        )

        for language, metadata, stream_url in grouped[sport]:

            name = get_channel_name(metadata)

            # Añadimos el idioma al nombre para identificar
            # fácilmente la procedencia lingüística.
            display_name = (
                f"[{language}] {name}"
            )

            output.append(
                f'#EXTINF:-1 '
                f'group-title="{sport}",'
                f'{display_name}'
            )

            output.append(stream_url)

            total += 1

        print(
            f"{sport}: "
            f"{len(grouped[sport])} canales"
        )

    output_text = "\n".join(output) + "\n"

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        file.write(output_text)

    print()
    print(
        f"Total incluidos en la parrilla: {total}"
    )

    print(
        f"Archivo creado: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
