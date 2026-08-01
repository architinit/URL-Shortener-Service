import re
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, redirect, render_template, request, current_app

from app import db, limiter
from app.models import Click, Link
from app.utils import short_code_for_id, hash_ip

bp = Blueprint("main", __name__)

URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$", re.IGNORECASE)
ALIAS_RE = re.compile(r"^[a-zA-Z0-9_-]{3,16}$")


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/api/shorten", methods=["POST"])
@limiter.limit("10 per minute")
def shorten():
    data = request.get_json(silent=True) or {}
    long_url = (data.get("long_url") or "").strip()
    custom_alias = (data.get("custom_alias") or "").strip()
    expires_in_days = data.get("expires_in_days")

    if not long_url or not URL_RE.match(long_url):
        return jsonify({"error": "Provide a valid http(s) URL"}), 400

    short_code = None
    if custom_alias:
        if not ALIAS_RE.match(custom_alias):
            return jsonify({"error": "Alias must be 3-16 chars: letters, numbers, - or _"}), 400
        if Link.query.filter_by(short_code=custom_alias).first():
            return jsonify({"error": "Alias already taken"}), 409
        short_code = custom_alias
        is_custom = True
    else:
        is_custom = False

    expires_at = None
    if expires_in_days:
        try:
            expires_at = datetime.utcnow() + timedelta(days=float(expires_in_days))
        except (TypeError, ValueError):
            return jsonify({"error": "expires_in_days must be a number"}), 400

    link = Link(short_code=short_code, long_url=long_url, expires_at=expires_at, is_custom_alias=is_custom)
    db.session.add(link)

    if not is_custom:
        db.session.flush()  # assigns link.id without committing
        link.short_code = short_code_for_id(link.id, length=current_app.config["SHORT_CODE_LENGTH"])
        short_code = link.short_code

    db.session.commit()

    return jsonify({
        "short_code": short_code,
        "short_url": request.host_url + short_code,
        "long_url": long_url,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }), 201


@bp.route("/<short_code>")
def resolve(short_code):
    link = Link.query.filter_by(short_code=short_code).first()
    if link is None:
        return jsonify({"error": "Short link not found"}), 404
    if link.is_expired():
        return jsonify({"error": "This link has expired"}), 410

    click = Click(
        link_id=link.id,
        referrer=request.referrer,
        user_agent=request.user_agent.string,
        ip_hash=hash_ip(request.remote_addr or "unknown"),
    )
    db.session.add(click)
    db.session.commit()

    return redirect(link.long_url, code=302)


@bp.route("/api/stats/<short_code>")
def stats(short_code):
    link = Link.query.filter_by(short_code=short_code).first()
    if link is None:
        return jsonify({"error": "Short link not found"}), 404

    recent_clicks = [
        {
            "clicked_at": c.clicked_at.isoformat(),
            "referrer": c.referrer,
            "user_agent": c.user_agent,
        }
        for c in link.clicks.order_by(Click.clicked_at.desc()).limit(20)
    ]

    payload = link.to_dict()
    payload["recent_clicks"] = recent_clicks
    return jsonify(payload)


@bp.route("/api/links")
def list_links():
    links = Link.query.order_by(Link.created_at.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in links])
