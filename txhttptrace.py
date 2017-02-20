from functools import wraps
from twisted.internet import defer
import uuid
import time
from urlparse import urlparse

"""
Endpoints decorated with @trace will add an extra parameter, ctx. ctx needs to be down-propagated to all
outgoing requests for request tracing.
The @profile decorator provides additional profiling capabilities to endpoints decorated with @trace.

Ex:
@app.route('/some/path', methods=['GET'])
@tracing.trace
@tracing.profile
def my_handler(ctx, request, ...):

"""


_logger = None
_debug = False
_exceptions_to_ignore = []
_log_errors_as_warnings = False

def set_logger(logger, log_errors_as_warnings=False):
    global _logger
    _logger = logger
    global _log_errors_as_warnings
    _log_errors_as_warnings = log_errors_as_warnings

def set_debug(debug):
    global _debug
    _debug = debug

def set_exceptions_to_ignore(*exceptions):
    global _exceptions_to_ignore
    for e in exceptions:
        if not issubclass(e, Exception):
            raise TypeError('%s is not an Exception' % e)
    _exceptions_to_ignore = exceptions


def trace(f):
    """
    Insert context into service and add request-id header for tracing.
    The request-id is extracted from the X-Request-ID header or, if not present, it is generated.
    """

    f = ensure_is_deferred(f)

    @wraps(f)
    @defer.inlineCallbacks
    def wrapper(request, *args, **kwargs):
        ctx = {'request-id': request.getHeader('X-Request-ID') or str(uuid.uuid4())}
        request.requestHeaders.addRawHeader('X-Request-ID', ctx['request-id'])
        res = yield f(ctx, request, *args, **kwargs)
        defer.returnValue(res)
    return wrapper


def profile(f):
    """
    Decorator for enabling basic instrumentation.
    The wrapped function now receives an additional parameter of type dictionary, ctx.
    Any entries added to ctx will be logged along with default logging fields:
    user_agent, endpoint path, and request duration.

    NOTE: This decorator requires the @trace decorator
    """

    assert(_logger is not None)

    f = ensure_is_deferred(f)

    @wraps(f)
    def wrapper(ctx, request, *args, **kwargs):

        ctx['user_agent'] = request.getHeader('User-Agent')
        ctx['endpoint'] = urlparse(request.uri).path
        start = time.time()

        def do_finally(param):
            ctx['took'] = time.time() - start
            if 'error' in ctx:
                msg = 'request failed'
                if _log_errors_as_warnings:
                    _logger.warn(msg, **ctx)
                else:
                    _logger.error(msg, **ctx)
            elif _debug:
                _logger.info('request successful', **ctx)
            return param

        def handle_error(failure):
            if not failure.check(*_exceptions_to_ignore):
                ctx['error'] = failure.getErrorMessage()
                ctx['traceback'] = str(failure.getTraceback(elideFrameworkCode=True, detail='brief'))
            return failure

        d = f(ctx, request, *args, **kwargs)
        d.addErrback(handle_error)
        d.addBoth(do_finally)
        return d

    return wrapper


def ensure_is_deferred(f):

    @wraps(f)
    def _ensure_is_deferred(*args, **kwargs):
        return defer.maybeDeferred(f, *args, **kwargs)

    return _ensure_is_deferred
