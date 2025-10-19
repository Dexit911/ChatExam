class AppError(Exception):
    """Base class for all ChatExam errors"""
    code = "GENERIC_ERROR"
    status_code = 500
    public = True

    # If not passing any message. Log __doc__ strings in the class
    def __init__(self, message=None, code=None, status_code=None, public=None):
        super().__init__(message or self.__doc__)
        self.message = message or self.__doc__
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        if public is not None:
            self.public = public

    # Example use: raise AppError("Something failed") -> console/loging -> [GENERIC ERROR] Something failed
    def __str__(self):
        return f"[{self.code}] {self.message}"


class AuthError(AppError):
    """User is not authorized to perform this action"""
    code = "AUTH_ERROR"
    status_code = 401


class DataError(AppError):
    """Database  operation failed"""
    code = "DB_ERROR"
    status_code = 500


class ValidationError(AppError):
    """Database validation failed"""
    code = "VALIDATION_ERROR"
    status_code = 400


"""Request"""


class RequestError(AppError):
    """Request failed"""
    code = "REQUEST_ERROR"
    status_code = 502


class TimeoutError(RequestError):
    """Request timed out"""
    code = "REQUEST_TIMEOUT"
    status_code = 408


"""GitHub exceptions"""


class EmptyRepo(RequestError):
    """Empty repository"""
    code = "EMPTY_REPO"
