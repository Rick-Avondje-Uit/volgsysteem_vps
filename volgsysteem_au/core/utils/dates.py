from datetime import date, datetime

DUTCH_DATE_FORMAT = "%d-%m-%Y"

def parse_dutch_date(value: str | None) -> date | None:
    """
    Zet een Nederlandse datumstring in dd-mm-jjjj-formaat
    om naar een datetime.date.

    Voorbeelden:
        "15-11-2026" -> date(2026, 11, 15)
        ""           -> None
        None         -> None

    Raises:
        ValueError: als de waarde geen geldige datum in
        dd-mm-jjjj-formaat is.
    """
    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    return datetime.strptime(
        value,
        DUTCH_DATE_FORMAT,
    ).date()

def parse_dutch_date_range(
    start_value: str | None,
    end_value: str | None,
) -> tuple[date | None, date | None]:
    start_date = parse_dutch_date(start_value)
    end_date = parse_dutch_date(end_value)

    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        raise ValueError(
            "De einddatum mag niet vóór de startdatum liggen."
        )

    return start_date, end_date

def format_dutch_date(value: date | None) -> str:
    if value is None:
        return ""

    return value.strftime(DUTCH_DATE_FORMAT)