from rest_framework.exceptions import APIException


class BusinessLogicError(APIException):
    status_code = 400
    default_detail = 'A business logic error occurred.'
    default_code = 'business_logic_error'


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable.'
    default_code = 'service_unavailable'