class DocumentError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DocumentNotFound(DocumentError):
    def __init__(self) -> None:
        super().__init__("Document not found", 404)
