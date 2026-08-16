from app.db.session import get_db


def get_current_user():
    return {"id": "SYSTEM_USER"}


__all__ = ["get_db", "get_current_user"]
