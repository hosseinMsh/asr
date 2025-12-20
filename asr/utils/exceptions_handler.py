import requests

class ASRBaseError(Exception):
    public_message = "خطای نامشخص"
    error_code = "UNKNOWN_ERROR"

class ASRTemporaryError(ASRBaseError):
    public_message = "سرویس موقتاً در دسترس نیست. بعداً تلاش کنید."
    error_code = "SERVICE_UNAVAILABLE"

class ASRBadInputError(ASRBaseError):
    public_message = "فایل صوتی معتبر نیست."
    error_code = "INVALID_AUDIO"

class ASRProcessingError(ASRBaseError):
    public_message = "خطا در پردازش صوت."
    error_code = "PROCESSING_FAILED"



def map_exception(e: Exception) -> ASRBaseError:
    if isinstance(e, requests.Timeout):
        return ASRTemporaryError()
    if isinstance(e, requests.ConnectionError):
        return ASRTemporaryError()
    if isinstance(e, requests.HTTPError):
        if e.response is not None and e.response.status_code == 400:
            return ASRBadInputError()
        return ASRProcessingError()
    return ASRProcessingError()
