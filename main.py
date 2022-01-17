from datetime import datetime, timedelta
from typing import Optional, Iterator

import databases
import enum

import jwt
import sqlalchemy
import uvicorn
from databases.backends.postgres import Record
from email_validator import EmailNotValidError, validate_email as ve

from fastapi import FastAPI, HTTPException, Depends
from decouple import config
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pydantic import BaseModel, validator

from passlib.context import CryptContext
from starlette.requests import Request

DATABASE_URL = (
    f"postgresql://{config('DB_USER')}:"
    f"{config('DB_PASSWORD')}@localhost:5433/clothes"
)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

app = FastAPI()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserRole(enum.Enum):
    super_admin = "super admin"
    admin = "admin"
    user = "user"


class ColorEnum(enum.Enum):
    pink = "pink"
    black = "black"
    white = "white"
    yellow = "yellow"


class SizeEnum(enum.Enum):
    xs = "xs"
    s = "s"
    m = "m"
    ll = "l"
    xl = "xl"
    xxl = "xxl"


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(120), unique=True),
    sqlalchemy.Column("password", sqlalchemy.String(255)),
    sqlalchemy.Column("full_name", sqlalchemy.String(200)),
    sqlalchemy.Column("phone", sqlalchemy.String(13)),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "last_modified_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "role",
        sqlalchemy.Enum(UserRole),
        nullable=False,
        server_default=UserRole.user.name,
    ),
)

clothes = sqlalchemy.Table(
    "clothes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(120)),
    sqlalchemy.Column("color", sqlalchemy.Enum(ColorEnum), nullable=False),
    sqlalchemy.Column("size", sqlalchemy.Enum(SizeEnum), nullable=False),
    sqlalchemy.Column("photo_url", sqlalchemy.String(255)),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "last_modified_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    ),
)


def is_admin(request: Request) -> None:
    user = request.state.user
    if not user or user["role"] not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(
            403, "You do not have permissions for this resource"
        )


def create_access_token(user: Record) -> Optional[str]:
    try:
        payload = {
            "sub": user["id"],
            "exp": datetime.utcnow() + timedelta(minutes=120),
        }
        return jwt.encode(payload, config("JWT_SECRET"), algorithm="HS256")
    except Exception:
        raise


class EmailField(str):
    @classmethod
    def __get_validators__(cls) -> Iterator:
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        try:
            ve(value)
            return value
        except EmailNotValidError:
            raise ValueError("Email is not valid")


class BaseUser(BaseModel):
    email: EmailField
    full_name: Optional[str]

    @validator("full_name")
    def validate_full_name(cls, value: str):
        try:
            assert len(value.split()) == 2
            return value
        except Exception:
            raise ValueError("You should provide at least two names")


class UserSignIn(BaseUser):
    password: str


class UserSignOut(BaseUser):
    phone: Optional[str]
    created_at: datetime
    last_modified_at: datetime


class ClothesBase(BaseModel):
    name: str
    color: str
    size: SizeEnum
    color: ColorEnum


class ClothesIn(ClothesBase):
    pass


class ClothesOut(ClothesBase):
    id: int
    created_at: datetime
    last_modified_at: datetime


class CustomHTTPBearer(HTTPBearer):
    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        res = await super().__call__(request)

        try:
            payload = jwt.decode(
                res.credentials, config("JWT_SECRET"), algorithms=["HS256"]
            )
            user = await database.fetch_one(
                users.select().where(users.c.id == payload["sub"])
            )
            request.state.user = user
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token is expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")


oauth2_scheme = CustomHTTPBearer()


@app.on_event("startup")
async def startup() -> None:
    await database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await database.disconnect()


@app.get("/clothes", dependencies=[Depends(oauth2_scheme)])
async def get_all_clothes() -> list:
    return await database.fetch_all(clothes.select())


@app.post(
    "/clothes",
    response_model=ClothesOut,
    dependencies=[Depends(oauth2_scheme), Depends(is_admin)],
    status_code=201,
)
async def create_clothes(clothes_data: ClothesIn) -> Record:
    id_ = await database.execute(clothes.insert().values(**clothes_data.dict()))
    return await database.fetch_one(clothes.select().where(clothes.c.id == id_))


@app.post("/register")
async def create_user(user: UserSignIn) -> dict:
    user.password = pwd_context.hash(user.password)
    q = users.insert().values(**user.dict())
    id_ = await database.execute(q)
    created_user = await database.fetch_one(
        users.select().where(users.c.id == id_)
    )
    token = create_access_token(created_user)
    return {"token": token}


if __name__ == "__main__":
    uvicorn.run(app)
