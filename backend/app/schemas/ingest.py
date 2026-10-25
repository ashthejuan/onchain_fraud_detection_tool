from pydantic import BaseModel


class RowError(BaseModel):
    row: int
    error: str


class IngestSummary(BaseModel):
    accepted: int
    rejected: int
    duplicates: int
    errors: list[RowError]
    errors_truncated: bool
