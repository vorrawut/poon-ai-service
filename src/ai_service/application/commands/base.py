"""Base classes for CQRS commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

# Type variables for command and result
TCommand = TypeVar("TCommand", bound="Command")
TResult = TypeVar("TResult")


@dataclass(frozen=True)
class Command(ABC):
    """
    Base class for all commands in the CQRS pattern.

    Commands represent intentions to change the state of the system.
    They should be immutable and contain all the data needed to
    perform the operation.
    """

    @abstractmethod
    def validate(self) -> None:
        """
        Validate command data.

        Raises:
            ValidationError: If command data is invalid
        """


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """
    Base class for command handlers.

    Command handlers contain the business logic for processing
    commands and coordinating with domain objects and repositories.
    """

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """
        Handle a command and return a result.

        Args:
            command: The command to handle

        Returns:
            The result of handling the command

        Raises:
            CommandHandlerError: If command handling fails
        """
        pass


@dataclass(frozen=True)
class CommandResult:
    """Result of executing a command."""

    success: bool
    message: str | None = None
    data: Any = None
    errors: list[str] | None = None

    @classmethod
    def success_result(
        cls, message: str | None = None, data: Any = None
    ) -> CommandResult:
        """Create a successful command result."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def failure_result(
        cls, message: str | None = None, errors: list[str] | None = None
    ) -> CommandResult:
        """Create a failed command result."""
        return cls(success=False, message=message, errors=errors)

    def is_success(self) -> bool:
        """Check if the command was successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if the command failed."""
        return not self.success
