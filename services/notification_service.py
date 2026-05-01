from datetime import datetime


class NotificationService:
    """Very simple in-memory notification store by user role."""

    def __init__(self):
        self._by_role: dict[str, list[dict]] = {
            "customer": [],
            "courier": [],
            "dispatcher": [],
        }

    def push(self, role: str, message: str) -> None:
        if role not in self._by_role:
            self._by_role[role] = []
        self._by_role[role].append(
            {
                "message": message,
                "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            }
        )

    def get_for_role(self, role: str) -> list[dict]:
        return list(self._by_role.get(role, []))
