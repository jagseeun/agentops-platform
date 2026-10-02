from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "agentops_http_requests_total",
    "Total number of HTTP requests",
    ["method", "route", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "agentops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"]
)

def record_http_request(
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
)->None:
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        route=route,
        status_code=str(status_code),
    ).inc()
    
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    ).observe(duration_seconds)
