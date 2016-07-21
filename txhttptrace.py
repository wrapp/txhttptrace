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


def set_logger(logger):
    global _logger
    _logger = logger


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
        res = yield f(ctx, request, *args, **kwargs)
        request.setHeader('X-Request-ID', ctx['request-id'])
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
                _logger.error('request failed', **ctx)
            else:
                _logger.info('request successful', **ctx)
            return param

        def handle_error(failure):
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
