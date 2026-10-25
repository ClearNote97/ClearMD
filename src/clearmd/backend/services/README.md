# src/clearmd/backend/services — Services (the ports' implementations)

The actors the use cases call through their ports: the markitdown adapter and own converters, format
detection, the worker process with its limits (ADR-0015), the settings store and the summary writer. The only
place where third-party libraries are imported.
