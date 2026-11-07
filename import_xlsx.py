from datetime import datetime
import openpyxl
from app import create_app, db
from app.models import MeterReading

app = create_app()

MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "decembre": 12,
}


def norm(s):
    return (
        str(s).lower()
        .replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("à", "a").replace("ô", "o").replace("î", "i")
        .replace("ï", "i").replace("û", "u").replace("ç", "c")
        .strip()
    )


def meter_from_label(label):
    l = norm(label)
    if "eau" in l:
        return "eau"
    if "gaz" in l:
        return "gaz"
    if "jour" in l:
        return "elec_jour"
    if "nuit" in l:
        return "elec_nuit"
    return None


def to_num(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def sheet_year(title):
    t = title.strip()
    if t.isdigit() and len(t) == 4:
        return int(t)
    return datetime.now().year


def import_sheet(ws, year):
    month_cols = {}
    for idx, cell in enumerate(ws[1]):
        if cell.value and norm(cell.value) in MONTHS:
            month_cols[idx] = MONTHS[norm(cell.value)]
    if not month_cols:
        return 0

    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        meter = meter_from_label(row[0]) if row and row[0] else None
        if not meter:
            continue
        for idx, month in month_cols.items():
            val = to_num(row[idx]) if idx < len(row) else None
            if val is None or val <= 0:
                continue
            existing = MeterReading.query.filter_by(
                year=year, month=month, meter=meter
            ).first()
            if existing:
                existing.value = val
            else:
                db.session.add(MeterReading(
                    year=year, month=month, meter=meter, value=val
                ))
            count += 1
    return count


def import_file(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    total = 0
    with app.app_context():
        for ws in wb.worksheets:
            total += import_sheet(ws, sheet_year(ws.title))
        db.session.commit()
        print(f"OK: {total} releves importes.")


if __name__ == "__main__":
    import_file("/app/data/conso-maison.xlsx")
