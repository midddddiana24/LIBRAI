from sqlalchemy.orm import Session
from backend.models.entities import Admin, AuditLog


def audit(db: Session, action: str, entity_type: str, entity_id=None, *, admin: Admin | None = None, actor_type="SYSTEM", actor_id=None, details=None) -> AuditLog:
    entry = AuditLog(admin_id=admin.id if admin else None, actor_type="ADMIN" if admin else actor_type, actor_id=str(admin.id if admin else actor_id) if (admin or actor_id) else None, action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None, details=details or {})
    db.add(entry)
    return entry
