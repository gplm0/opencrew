from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import aiosqlite

from config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        expiration_hours: Optional[int] = None,
        db_path: str = "jarvis.db",
    ):
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.expiration_hours = expiration_hours or settings.JWT_EXPIRATION_HOURS
        self.db_path = db_path

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_token(self, user_id: str, username: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, username, email, hashed_password, is_active FROM users WHERE username = ?",
                (username,),
            ) as cursor:
                user = await cursor.fetchone()

                if not user or not user["is_active"]:
                    return None

                if not self.verify_password(password, user["hashed_password"]):
                    return None

                token = self.create_token(user["id"], user["username"])

                # Save session
                from uuid import uuid4
                session_id = str(uuid4())
                expires_at = datetime.utcnow() + timedelta(hours=self.expiration_hours)
                
                await db.execute(
                    "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
                    (session_id, user["id"], token, expires_at.isoformat()),
                )
                await db.commit()

                return {
                    "user_id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "token": token,
                }

    async def create_user(
        self, user_id: str, username: str, email: str, password: str
    ) -> Dict[str, Any]:
        hashed_password = self.hash_password(password)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (id, username, email, hashed_password) VALUES (?, ?, ?, ?)",
                (user_id, username, email, hashed_password),
            )
            await db.commit()

        token = self.create_token(user_id, username)

        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "token": token,
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = self.decode_token(token)

            # Check if session exists and is valid
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT id FROM sessions WHERE token = ? AND expires_at > ?",
                    (token, datetime.utcnow().isoformat()),
                ) as cursor:
                    session = await cursor.fetchone()

                    if not session:
                        return None

                    return payload
        except ValueError:
            return None

    async def revoke_token(self, token: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            await db.commit()
            return True
