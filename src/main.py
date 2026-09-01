import sys
from pathlib import Path

# Permite importar los módulos que están dentro de src/
SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from sports import SPORTS
from epg import download_epg, parse_epg
from streams import (
    download_streams,
    group_streams_by_channel,
    remove_duplicate_streams,
)
from m3u import save_m3u


def normalize(text):
    if not text:
        return ""

    return str(text).lower().strip()


def detect_sport_from_text(text):
    """
    Detecta el deporte a partir del título y descripción
    de la programación EPG.
    """

    text = normalize(text)

    for sport_id, sport_data in SPORTS.items():

        for keyword in sport_data["keywords"]:

            if keyword in text:
                return sport_id

    return None


def build_events(programs, streams_by_channel):
    """
    Relaciona programas de la EPG con los streams del canal.

    Importante:
    La EPG identifica qué programa está anunciado para el canal.
    El stream queda asociado al canal correspondiente.
    """

    events = []

    for program in programs:

        title = program.get(
            "title",
            ""
        )

        description = program.get(
            "description",
            ""
        )

        text = (
            title
            + " "
            + description
        )

        sport_id = detect_sport_from_text(
            text
        )

        if sport_id is None:
            continue

        channel_id = program.get(
            "channel",
            ""
        )

        if not channel_id:
            continue

        channel_streams = (
            streams_by_channel.get(
                channel_id,
                []
            )
        )

        if not channel_streams:
            continue

        stream_list = []

        for stream in channel_streams:

            url = stream.get(
                "url"
            )

            if not url:
                continue

            stream_list.append({
                "url": url,
                "name": stream.get(
                    "title",
                    "Fuente"
                ),
            })

        stream_list = remove_duplicate_streams(
            stream_list
        )

        if not stream_list:
            continue

        # Nombre del evento.
        event_name = title

        if description:
            event_name = (
                f"{title} - {description}"
            )

        # Convertir el identificador del deporte
        # al nombre utilizado por m3u.py.
        sport_name = SPORTS[
            sport_id
        ]["name"]

        events.append({
            "sport": sport_name,
            "name": event_name,
            "channel": channel_id,
            "streams": stream_list,
            "start": program.get(
                "start",
                ""
            ),
            "stop": program.get(
                "stop",
                ""
            ),
        })

    return events


def main():

    print("=" * 60)
    print("DEPORTES MAESTRO")
    print("Actualizador de eventos deportivos")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Descargar EPG
    # --------------------------------------------------------

    print()
    print("1/4 - Descargando EPG...")

    epg_data = download_epg()

    programs = parse_epg(
        epg_data
    )

    print(
        f"Programas encontrados: "
        f"{len(programs)}"
    )

    # --------------------------------------------------------
    # 2. Descargar streams
    # --------------------------------------------------------

    print()
    print("2/4 - Descargando streams...")

    streams = download_streams()

    print(
        f"Streams recibidos: "
        f"{len(streams)}"
    )

    # --------------------------------------------------------
    # 3. Agrupar streams
    # --------------------------------------------------------

    print()
    print("3/4 - Preparando fuentes...")

    streams_by_channel = (
        group_streams_by_channel(
            streams
        )
    )

    # --------------------------------------------------------
    # 4. Relacionar EPG + streams
    # --------------------------------------------------------

    print()
    print("4/4 - Creando eventos...")

    events = build_events(
        programs,
        streams_by_channel
    )

    print(
        f"Eventos encontrados: "
        f"{len(events)}"
    )

    # --------------------------------------------------------
    # Mostrar resumen
    # --------------------------------------------------------

    print()

    for sport_id, sport_data in SPORTS.items():

        sport_name = sport_data[
            "name"
        ]

        count = sum(
            1
            for event in events
            if event.get("sport")
            == sport_name
        )

        print(
            f"{sport_name}: "
            f"{count} eventos"
        )

    # --------------------------------------------------------
    # Generar M3U
    # --------------------------------------------------------

    print()
    print("Generando parrilla M3U...")

    output_file = save_m3u(
        events
    )

    print()
    print(
        f"Archivo generado: "
        f"{output_file}"
    )

    print("=" * 60)
    print("PROCESO TERMINADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
