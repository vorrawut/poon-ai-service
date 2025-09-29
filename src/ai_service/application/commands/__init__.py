"""Command handlers for CQRS pattern."""

from .base import Command, CommandHandler
from .spending_commands import (
    CreateSpendingEntryCommand,
    CreateSpendingEntryCommandHandler,
    DeleteSpendingEntryCommand,
    DeleteSpendingEntryCommandHandler,
    EnhanceWithAICommand,
    EnhanceWithAICommandHandler,
    ProcessImageCommand,
    ProcessImageCommandHandler,
    ProcessTextCommand,
    ProcessTextCommandHandler,
    UpdateSpendingEntryCommand,
    UpdateSpendingEntryCommandHandler,
)

__all__ = [
    "Command",
    "CommandHandler",
    "CreateSpendingEntryCommand",
    "CreateSpendingEntryCommandHandler",
    "DeleteSpendingEntryCommand",
    "DeleteSpendingEntryCommandHandler",
    "EnhanceWithAICommand",
    "EnhanceWithAICommandHandler",
    "ProcessImageCommand",
    "ProcessImageCommandHandler",
    "ProcessTextCommand",
    "ProcessTextCommandHandler",
    "UpdateSpendingEntryCommand",
    "UpdateSpendingEntryCommandHandler",
]
