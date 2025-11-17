"""Base query and query handler interfaces.

Queries represent read operations (no state changes) in CQRS pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from returns.result import Result

# Query type
TQuery = TypeVar("TQuery", bound="Query")
# Query result type
TResult = TypeVar("TResult")


class Query(BaseModel):
    """Base class for all queries.

    Queries are read operations that don't change system state.
    They should be immutable (Pydantic models with frozen=True).

    Examples:
        class GetMessageHistoryQuery(Query):
            chat_id: int
            limit: int = 50
    """

    class Config:
        frozen = True  # Queries are immutable


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Base class for query handlers.

    Each query has exactly one handler that executes the query.

    Handlers return Result monads for consistent error handling.

    Examples:
        class GetMessageHistoryQueryHandler(QueryHandler[GetMessageHistoryQuery, list[MessageDTO]]):
            async def handle(self, query: GetMessageHistoryQuery) -> Result[list[MessageDTO], Error]:
                # Execute query logic
                ...
                return Success(messages)
    """

    @abstractmethod
    async def handle(self, query: TQuery) -> Result[TResult, Exception]:
        """Handle the query.

        Args:
            query: Query to execute

        Returns:
            Result with query result or error
        """
        ...
