class APIError(Exception):
    def __init__(self, message, status_code=400, code="BAD_REQUEST", developer_hint=False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.developer_hint = developer_hint
