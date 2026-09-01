from pathlib import Path


OUTPUT_FILE = Path(
    "output/parrilla_deportes_automatica.m3u"
)


SPORT_ORDER = [
    "1. FÚTBOL",
    "2. TENIS",
    "3. BALONCESTO",
    "4. FÓRMULA 1",
    "5. MOTOGP",
]


def clean_text(text):
    """
    Limpia texto para utilizarlo en una entrada M3U.
    """

    if text is None:
        return ""

    return str(text).strip()


def create_m3u(events):
    """
    Genera el contenido M3U a partir de eventos.

    Cada evento puede contener varias fuentes.
    """

    lines = [
        "#EXTM3U",
        ""
    ]

    for sport in SPORT_ORDER:

        lines.append(
            f"# ===== {sport} ====="
        )

        sport_events = [
            event
            for event in events
            if event.get("sport") == sport
        ]

        for event in sport_events:

            event_name = clean_text(
                event.get(
                    "name",
                    "Evento deportivo"
                )
            )

            streams = event.get(
                "streams",
                []
            )

            for index, stream in enumerate(
                streams,
                start=1
            ):

                url = clean_text(
                    stream.get("url")
                )

                if not url:
                    continue

                source_name = clean_text(
                    stream.get(
                        "name",
                        f"Fuente {index}"
                    )
                )

                display_name = (
                    f"{event_name} | "
                    f"{source_name}"
                )

                lines.append(
                    f'#EXTINF:-1 '
                    f'group-title="{sport}",'
                    f'{display_name}'
                )

                lines.append(url)

        lines.append("")

    return "\n".join(lines)


def save_m3u(events):
    """
    Guarda la parrilla M3U en output/.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    content = create_m3u(
        events
    )

    OUTPUT_FILE.write_text(
        content,
        encoding="utf-8"
    )

    return OUTPUT_FILE
