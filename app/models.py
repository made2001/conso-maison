from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class MeterReading(db.Model):
    """Relevé mensuel (valeur cumulée) pour un compteur."""
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    meter = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("year", "month", "meter", name="uq_reading"),
    )

    @property
    def consumption(self):
        prev_year, prev_month = (
            (self.year - 1, 12) if self.month == 1 else (self.year, self.month - 1)
        )
        prev = MeterReading.query.filter_by(
            year=prev_year, month=prev_month, meter=self.meter
        ).first()
        if prev:
            return round(self.value - prev.value, 2)
        return None


class CostConfig(db.Model):
    """Prix unitaire par compteur."""
    id = db.Column(db.Integer, primary_key=True)
    meter = db.Column(db.String(20), unique=True, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    label = db.Column(db.String(50), nullable=False)


