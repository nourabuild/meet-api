from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

ERROR_MAP = {
    # String
    'string_type': 'MUST_BE_STRING',
    'string_too_short': 'TOO_SHORT',
    'string_too_long': 'TOO_LONG',
    'string_pattern_mismatch': 'INVALID_FORMAT',
    'string_unicode': 'INVALID_UNICODE',

    # Number
    'int_type': 'MUST_BE_INTEGER',
    'int_parsing': 'MUST_BE_INTEGER',
    'int_from_float': 'MUST_BE_INTEGER',
    'float_type': 'MUST_BE_NUMBER',
    'float_parsing': 'MUST_BE_NUMBER',
    'greater_than': 'TOO_SMALL',
    'greater_than_equal': 'OUT_OF_RANGE',
    'less_than': 'TOO_LARGE',
    'less_than_equal': 'OUT_OF_RANGE',
    'multiple_of': 'INVALID_MULTIPLE',
    'finite_number': 'MUST_BE_FINITE',

    # Bool
    'bool_type': 'MUST_BE_BOOLEAN',
    'bool_parsing': 'MUST_BE_BOOLEAN',

    # DateTime
    'datetime_type': 'INVALID_DATETIME',
    'datetime_parsing': 'INVALID_DATETIME',
    'datetime_from_date_parsing': 'INVALID_DATETIME',
    'date_type': 'INVALID_DATE',
    'date_parsing': 'INVALID_DATE',
    'date_from_datetime_parsing': 'INVALID_DATE',
    'time_type': 'INVALID_TIME',
    'time_parsing': 'INVALID_TIME',
    'datetime_future': 'MUST_BE_FUTURE',
    'datetime_past': 'MUST_BE_PAST',
    'date_future': 'MUST_BE_FUTURE',
    'date_past': 'MUST_BE_PAST',
    'timezone_naive': 'TIMEZONE_REQUIRED',
    'timezone_aware': 'TIMEZONE_NOT_ALLOWED',

    # Collections
    'list_type': 'MUST_BE_LIST',
    'tuple_type': 'MUST_BE_LIST',
    'set_type': 'MUST_BE_LIST',
    'frozenset_type': 'MUST_BE_LIST',
    'dict_type': 'MUST_BE_OBJECT',
    'too_short': 'TOO_FEW_ITEMS',
    'too_long': 'TOO_MANY_ITEMS',

    # Email/URL
    'email_type': 'INVALID_EMAIL',
    'url_type': 'INVALID_URL',
    'url_parsing': 'INVALID_URL',
    'url_scheme': 'INVALID_URL',
    'url_too_long': 'INVALID_URL',
    'url_host_required': 'INVALID_URL',
    'url_port': 'INVALID_URL',

    # UUID
    'uuid_type': 'INVALID_UUID',
    'uuid_parsing': 'INVALID_UUID',

    # JSON
    'json_invalid': 'INVALID_JSON',
    'json_type': 'INVALID_JSON',

    # General
    'missing': 'REQUIRED',
    'extra_forbidden': 'NOT_ALLOWED',
    'literal_error': 'INVALID_CHOICE',
    'enum_error': 'INVALID_CHOICE',
    'none_required': 'MUST_BE_NULL',
    'none_not_allowed': 'CANNOT_BE_NULL',
    'assertion_error': 'ASSERTION_FAILED',
}

async def request_validation_error(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        loc = err.get("loc", [])
        field = loc[-1] if loc else "unknown"
        type_ = err.get("type", "")
        msg = err.get("msg", "").lower()

        # Try direct map
        key = ERROR_MAP.get(type_)

        # Handle value_error type specially (email/url in msg)
        if not key and type_ == "value_error":
            if "email" in msg:
                key = "INVALID_EMAIL"
            elif "url" in msg:
                key = "INVALID_URL"
            else:
                key = "INVALID_VALUE"

        # Fallback
        if not key:
            key = "INVALID"

        errors[field] = f"VALIDATION_{field.upper()}_{key}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )

async def http_validation_error(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"errors": exc.detail}
        )

    message = str(exc.detail).strip().rstrip(".!?,")
    normalized = f"VALIDATION_ERROR_{message.replace(' ', '_').upper()}"

    return JSONResponse(
        status_code=exc.status_code,
        content={"errors": normalized}
    )

