# txhttptrace

Provides decorators for endpoint tracing and profiling.

## Usage
Endpoints decorated with @trace will add an extra parameter for the 
context, ctx. ctx needs to be down-propagated to all outgoing requests 
for request tracing.
The @profile decorator provides additional profiling capabilities to 
endpoints decorated with @trace.

Ex:
```
@app.route('/some/path', methods=['GET'])
@tracing.trace
@tracing.profile
def my_handler(ctx, request, ...):
    pass
```