"""Typed CLI errors. Each error maps to a documented exit code (spec §6)."""


class CLIError(Exception):
    exit_code: int = 1


class ValidationError(CLIError):
    exit_code = 2


class NotFoundError(CLIError):
    exit_code = 1


class IllegalTransitionError(CLIError):
    exit_code = 1


class StoreError(CLIError):
    exit_code = 3
