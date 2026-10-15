class AIServiceError(Exception):
    """Controlled error exposed by the AI orchestration layer."""

    def __init__(self, message: str, *, code: str = "ai_service_error"):
        super().__init__(message)
        self.code = code
