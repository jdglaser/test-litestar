from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_409_CONFLICT


class UserAlreadyExistsException(HTTPException):
    status_code = HTTP_409_CONFLICT
