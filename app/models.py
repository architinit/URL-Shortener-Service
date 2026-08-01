from datetime import datetime

from app import db


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(16), unique=True, nullable=True, index=True)
    long_url = db.Column(db.String(2048), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_custom_alias = db.Column(db.Boolean, default=False)

    clicks = db.relationship("Click", backref="link", lazy="dynamic", cascade="all, delete-orphan")

    def is_expired(self):
        return self.expires_at is not None and datetime.utcnow() > self.expires_at

    def to_dict(self):
        return {
            "short_code": self.short_code,
            "long_url": self.long_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "click_count": self.clicks.count(),
        }


class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey("link.id"), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    referrer = db.Column(db.String(512), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)
