# services/auth_service.py

MOCK_USERS = [
    {"email": "customer1@test.com", "password": "1234", "role": "customer", "name": "Jana Nováková"},
    {"email": "customer2@test.com", "password": "1234", "role": "customer", "name": "Peter Horváth"},
    {"email": "courier1@test.com",  "password": "1234", "role": "courier",  "name": "Marek Sloboda", "id": "123456"},
    {"email": "courier2@test.com",  "password": "1234", "role": "courier",  "name": "Tomáš Kováč", "id": "654321"},
]

class AuthService:
    def __init__(self):
        self.current_user = None

    def login(self, email: str, password: str) -> dict:
        email = email.strip().lower()

        user = next((u for u in MOCK_USERS if u["email"] == email), None)

        if user is None:
            return {"success": False, "error": "Email neexistuje"}

        if user["password"] != password:
            return {"success": False, "error": "Nesprávne heslo"}

        self.current_user = user
        return {"success": True, "role": user["role"], "name": user["name"], "id": user.get("id", "")}

    def logout(self):
        self.current_user = None

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    @property
    def role(self):
        return self.current_user["role"] if self.current_user else None