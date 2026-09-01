from datetime import datetime, timezone


def get_current_time():
    """
    Devuelve la fecha y hora actual en UTC.
    """
    return datetime.now(timezone.utc)


def get_live_events():
    """
    Punto de entrada para obtener los eventos deportivos
    disponibles.

    Más adelante conectaremos aquí la fuente de eventos.
    Por ahora devuelve una lista vacía para que el proyecto
    pueda construirse por módulos sin errores.
    """
    return []


def filter_live_events(events):
    """
    Conserva únicamente eventos que estén marcados
    como activos/en directo.
    """
    live_events = []

    for event in events:
        if event.get("live") is True:
            live_events.append(event)

    return live_events
