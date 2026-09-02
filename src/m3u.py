from pathlib import Path


OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "output"
    / "parrilla_deportes_automatica.m3u"
)


SPORT_ORDER = [
    "FÚTBOL",
    "TENIS",
    "BALONCESTO",
    "FÓRMULA 1",
    "MOTOGP",
]


def clean_text(text):
    if text is None:
        return ""

    return (
        str(text)
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def create_m3u(events):
    """
    Crea una M3U deportiva.

    Todos los eventos pertenecen al grupo principal DEPORTES.
    El deporte aparece dentro del nombre del evento.
    Cada evento mantiene todas sus fuentes disponibles.
    """

    lines = [
        "#EXTM3U",
        ""
    ]

    for sport_name in SPORT_ORDER:

        sport_events = [
            event
            for event in events
            if event.get("sport_name") == sport_name
        ]

        seen_events = set()

        for event in sport_events:

            title = clean_text(
                event.get(
                    "title",
                    "Evento deportivo"
                )
            )

            start = clean_text(
                event.get(
                    "start",
                    ""
                )
            )

            event_key = f"{sport_name}|{title}|{start}"

            if event_key in seen_events:
                continue

            seen_events.add(event_key)

            servers = event.get(
                "servers",
                []
            )

            seen_urls = set()
            server_number = 0

            for server in servers:

                url = clean_text(
                    server.get("url")
                )

                if not url:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                server_number += 1

                server_name = clean_text(
                    server.get(
                        "name",
                        ""
                    )
                )

                if not server_name:
                    server_name = (
                        f"Servidor "
                        f"{server_number}"
                    )

                display_name = (
                    f"{sport_name} | "
                    f"{title} | "
                    f"{server_name}"
                )

                lines.append(
                    f'#EXTINF:-1 '
                    f'group-title="DEPORTES",'
                    f'{display_name}'
                )

                lines.append(url)

            lines.append("")

    return "\n".join(lines)


def save_m3u(events):
    """
    Guarda la parrilla generada en output/.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    content = create_m3u(events)

    OUTPUT_FILE.write_text(
        content,
        encoding="utf-8",
        newline="\n"
    )

    print(
        f"M3U guardada en: "
        f"{OUTPUT_FILE}"
    )

    return OUTPUT_FILE
