import uuid


class FixtureCommsAdapter:
    def queue_member_letter(self, claim_id: uuid.UUID, subject: str, body: str) -> dict:
        return {
            "claim_id": str(claim_id),
            "queued": True,
            "sent": False,
            "subject": subject,
            "body": body,
        }
