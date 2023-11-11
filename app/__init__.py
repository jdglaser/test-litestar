import enum
import logging
import random
import string
from datetime import datetime, timedelta
from http.client import HTTPException
from typing import Callable, Optional, TypeVar

from argon2 import PasswordHasher
from attr import define
from litestar import Controller, Litestar, Request, Response, Router, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException, NotFoundException
from litestar.logging import LoggingConfig
from litestar.static_files import StaticFilesConfig
from litestar.status_codes import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.types import ASGIApp, Receive, Scope, Send

T = TypeVar("T")


def find_first(list: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    found_item = [i for i in list if predicate(i)]
    if len(found_item) == 0:
        return None
    return found_item[0]


@define
class Order:
    order_id: int
    order_total: float


@define
class CreateOrderRequest:
    order_total: float


@define
class User:
    user_id: int
    email: str
    hashed_password: str
    created_at: datetime


@define
class CreateUserRequest:
    email: str
    password: str


@define
class LoginUserRequest:
    email: str
    password: str


class TokenType(enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@define
class Token:
    token_id: int
    type: TokenType
    value: str
    user_id: int
    active: bool
    expires_at: datetime
    created_at: datetime
    deactivated_at: Optional[datetime]


class DataStore:
    def __init__(self) -> None:
        self.order_id = 1
        self.orders: list[Order] = []
        self.users: list[User] = []
        self.tokens: list[Token] = []


class OrderController(Controller):
    path = "/orders"

    @get()
    async def get_orders(self, data_store: DataStore) -> list[Order]:
        return data_store.orders

    @post(status_code=HTTP_201_CREATED)
    async def create_order(self, data: CreateOrderRequest, data_store: DataStore) -> Order:
        new_order = Order(data_store.order_id, data.order_total)
        data_store.orders.append(new_order)
        data_store.order_id = data_store.order_id + 1
        return new_order

    @get("/{order_id:int}")
    async def get_order(self, order_id: int, data_store: DataStore) -> Response:
        found_order = find_first(data_store.orders, lambda order: order.order_id == order_id)
        if not found_order:
            raise NotFoundException(detail="Order not found")
        return Response(found_order)


class EmailAlreadyExistsException(HTTPException):
    status_code = HTTP_401_UNAUTHORIZED


async def password_hasher_dep(state: State) -> PasswordHasher:
    return state.password_hasher


@define
class LoginUserResponse:
    access_token: str
    refresh_token: str


class AuthController(Controller):
    path = "/auth"
    dependencies = {"password_hasher": Provide(password_hasher_dep)}

    @post("/register")
    async def register(
        self, data: CreateUserRequest, data_store: DataStore, password_hasher: PasswordHasher
    ) -> Response:
        if data.email in [u.email for u in data_store.users]:
            raise EmailAlreadyExistsException(f"User with email '{data.email}' already exists")

        hashed_password = password_hasher.hash(data.password)
        new_user = User(
            user_id=len(data_store.users) + 1,
            email=data.email,
            hashed_password=hashed_password,
            created_at=datetime.now(),
        )

        data_store.users.append(new_user)
        return Response(None, status_code=HTTP_201_CREATED)

    @post("/login")
    async def login(
        self,
        data: LoginUserRequest,
        data_store: DataStore,
        password_hasher: PasswordHasher,
        request: Request,
    ) -> LoginUserResponse:
        stored_user = find_first(data_store.users, lambda user: user.email == data.email)
        if not stored_user:
            raise NotAuthorizedException("Incorrect email or password")
        try:
            password_hasher.verify(stored_user.hashed_password, data.password)
        except Exception:
            raise NotAuthorizedException("Incorrect email or password")
        if password_hasher.check_needs_rehash(stored_user.hashed_password):
            request.logger.info("Rehashing user password")
            new_hashed_password = password_hasher.hash(data.password)
            stored_user.hashed_password = new_hashed_password
            data_store.users[data_store.users.index(stored_user)] = stored_user

        access_token = Token(
            token_id=len(data_store.tokens),
            type=TokenType.ACCESS,
            value="".join(random.choices(string.ascii_letters + string.digits, k=32)),
            user_id=stored_user.user_id,
            active=True,
            expires_at=datetime.now() + timedelta(minutes=5),
            created_at=datetime.now(),
            deactivated_at=None,
        )

        data_store.tokens.append(access_token)

        refresh_token = Token(
            token_id=len(data_store.tokens),
            type=TokenType.REFRESH,
            value="".join(random.choices(string.ascii_letters + string.digits, k=32)),
            user_id=stored_user.user_id,
            active=True,
            expires_at=datetime.now() + timedelta(days=7),
            created_at=datetime.now(),
            deactivated_at=None,
        )

        data_store.tokens.append(refresh_token)

        return LoginUserResponse(access_token=access_token.value, refresh_token=refresh_token.value)


async def startup(app: Litestar) -> None:
    app.state.data_store = DataStore()
    app.state.password_hasher = PasswordHasher()


async def data_store_dep(state: State) -> DataStore:
    return state.data_store


def auth_middleware_factory(app: ASGIApp) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request = Request(scope)
            auth_header = request.headers.get("Authorization", None)
            if not auth_header:
                raise NotAuthorizedException("Missing authorization header")
        await app(scope, receive, send)

    return my_middleware


log_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.DEBUG), "handlers": ["console"]},
)


async def log_exception(exception: Exception, scope: Scope) -> None:
    request: Request = Request(scope)
    request.logger.exception(str(exception))


protected_router = Router("/", route_handlers=[OrderController])  # , middleware=[auth_middleware_factory])
api_router = Router("/api", route_handlers=[protected_router, AuthController])
app = Litestar(
    route_handlers=[api_router],
    on_startup=[startup],
    dependencies={"data_store": Provide(data_store_dep)},
    static_files_config=[StaticFilesConfig(path="/", directories=["app/static"], html_mode=True)],
    logging_config=log_config,
    after_exception=[log_exception],
)
