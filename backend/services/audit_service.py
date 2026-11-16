from models.audit_event import AuditEvent


def record_audit(

    db,

    invoice_id,

    actor_id,

    action,

    outcome,

    details=None

):

    event = AuditEvent(

        invoice_id=invoice_id,

        actor_id=actor_id,

        action=action,

        outcome=outcome,

        details=details or {}
    )

    db.add(event)

    return event