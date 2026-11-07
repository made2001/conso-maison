import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import MeterReading, CostConfig

main_bp = Blueprint("main", __name__)

METERS = {
    "eau": "Eau (m3)",
    "gaz": "Gaz (m3)",
    "elec_jour": "Elec Jour (kWh)",
    "elec_nuit": "Elec Nuit (kWh)",
}


@main_bp.route("/")
@login_required
def dashboard():
    years = db.session.query(MeterReading.year).distinct().order_by(
        MeterReading.year.desc()
    ).all()
    years = [y[0] for y in years]
    selected_year = request.args.get("year", type=int) or (
        years[0] if years else datetime.now().year
    )

    readings = MeterReading.query.filter_by(year=selected_year).all()
    by_meter = {}
    for r in readings:
        by_meter.setdefault(r.meter, {})[r.month] = r

    monthly = []
    for m in range(1, 13):
        row = {"month": m}
        for meter_key in METERS:
            reading = by_meter.get(meter_key, {}).get(m)
            if reading:
                row[meter_key] = reading.consumption
            else:
                row[meter_key] = None
        if row.get("elec_jour") is not None and row.get("elec_nuit") is not None:
            row["elec_total"] = round(row["elec_jour"] + row["elec_nuit"], 2)
        else:
            row["elec_total"] = None
        monthly.append(row)

    costs = CostConfig.query.all()
    cost_map = {c.meter: c for c in costs}

    annual = {}
    for meter_key in METERS:
        values = [r[meter_key] for r in monthly if r.get(meter_key) is not None]
        total = sum(values)
        count = len(values)
        annual[meter_key] = round(total, 2) if total else 0
        annual[f"{meter_key}_avg"] = round(total / count, 2) if count else 0
        annual[f"{meter_key}_months"] = count
        if meter_key in cost_map and total:
            annual[f"{meter_key}_cost"] = round(total * cost_map[meter_key].unit_price, 2)

    return render_template(
        "dashboard.html",
        years=years,
        selected_year=selected_year,
        monthly=monthly,
        meters=METERS,
        annual=annual,
        cost_map=cost_map,
    )


@main_bp.route("/entries", methods=["GET", "POST"])
@login_required
def entries():
    year = request.args.get("year", type=int) or datetime.now().year
    if request.method == "POST":
        y = int(request.form["year"])
        m = int(request.form["month"])
        meter = request.form["meter"]
        value = float(request.form["value"])
        existing = MeterReading.query.filter_by(year=y, month=m, meter=meter).first()
        if existing:
            existing.value = value
        else:
            db.session.add(MeterReading(year=y, month=m, meter=meter, value=value))
        db.session.commit()
        flash("Releve enregistre.", "success")
        return redirect(url_for("main.entries", year=y))

    readings = MeterReading.query.filter_by(year=year).all()
    by_meter = {}
    for r in readings:
        by_meter.setdefault(r.meter, {})[r.month] = r.value

    return render_template("entries.html", year=year, meters=METERS, by_meter=by_meter)


@main_bp.route("/costs", methods=["GET", "POST"])
@login_required
def costs():
    if request.method == "POST":
        for meter_key in METERS:
            price = request.form.get(f"price_{meter_key}", "").strip()
            if price:
                config = CostConfig.query.filter_by(meter=meter_key).first()
                if config:
                    config.unit_price = float(price)
                else:
                    db.session.add(CostConfig(
                        meter=meter_key,
                        unit_price=float(price),
                        label=METERS[meter_key],
                    ))
        db.session.commit()
        flash("Prix mis a jour.", "success")
        return redirect(url_for("main.costs"))

    configs = CostConfig.query.all()
    config_map = {c.meter: c for c in configs}
    return render_template("costs.html", meters=METERS, config_map=config_map)


@main_bp.route("/import", methods=["GET", "POST"])
@login_required
def import_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".csv"):
            flash("Merci de fournir un fichier CSV.", "danger")
            return redirect(url_for("main.import_csv"))

        content = file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content), delimiter=";")
        next(reader, None)
        count = 0
        for row in reader:
            if len(row) < 4:
                continue
            try:
                year = int(row[0])
                month = int(row[1])
                meter = row[2].strip()
                value = float(row[3].replace(",", "."))
            except ValueError:
                continue
            existing = MeterReading.query.filter_by(
                year=year, month=month, meter=meter
            ).first()
            if existing:
                existing.value = value
            else:
                db.session.add(MeterReading(
                    year=year, month=month, meter=meter, value=value
                ))
            count += 1
        db.session.commit()
        flash(f"{count} releves importes.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("import.html")


@main_bp.route("/api/chart/<int:year>")
@login_required
def chart_data(year):
    readings = MeterReading.query.filter_by(year=year).all()
    by_meter = {}
    for r in readings:
        by_meter.setdefault(r.meter, {})[r.month] = r.consumption

    result = {"months": list(range(1, 13))}
    for meter_key in METERS:
        result[meter_key] = [by_meter.get(meter_key, {}).get(m) for m in range(1, 13)]

    return result
