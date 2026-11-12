
class ApplicationError(Exception):
    """
    Base exception for expected application-level failures.

    Messages must be safe for exposure to API consumers.
    Never pass raw database or third-party provider errors here.
    """

    code = "APPLICATION_ERROR"
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(ApplicationError):
    code = "BAD_REQUEST"
    status_code = 400


class ResourceNotFoundError(ApplicationError):
    code = "RESOURCE_NOT_FOUND"
    status_code = 404


class ConflictError(ApplicationError):
    code = "CONFLICT"
    status_code = 409


class ExternalServiceError(ApplicationError):
    code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502


class ServiceUnavailableError(ApplicationError):
    code = "SERVICE_UNAVAILABLE"
    status_code = 503
