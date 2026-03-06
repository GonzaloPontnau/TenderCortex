"""Modulo de tracing con Arize Phoenix para observabilidad local.

Configura OpenTelemetry con exportador OTLP hacia un servidor Phoenix local.
Todos los imports de OTel/Phoenix son lazy (dentro del cuerpo de la funcion)
para evitar overhead en produccion cuando el tracing esta deshabilitado.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)

_TRACING_INITIALIZED: bool = False


def setup_phoenix_tracing(endpoint: str) -> None:
    """Configura OpenTelemetry TracerProvider con exportador OTLP hacia Phoenix.

    Args:
        endpoint: URL del endpoint OTLP HTTP de Phoenix.

    Raises:
        ImportError: Si los paquetes de tracing no estan instalados
                     (capturado internamente, loguea warning).
    """
    global _TRACING_INITIALIZED

    if _TRACING_INITIALIZED:
        logger.info("Phoenix tracing ya inicializado, omitiendo configuracion duplicada")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from openinference.instrumentation.langchain import LangChainInstrumentor
    except ImportError:
        logger.warning(
            "Paquetes de tracing (opentelemetry/phoenix) no instalados. "
            "Ejecuta 'pip install -r requirements-tracing.txt' para habilitar tracing."
        )
        return

    resource = Resource.create({"service.name": "tendercortex-backend"})
    exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = SimpleSpanProcessor(exporter)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)

    LangChainInstrumentor().instrument()

    _TRACING_INITIALIZED = True
    logger.info(f"Phoenix tracing activo -> {endpoint}")
