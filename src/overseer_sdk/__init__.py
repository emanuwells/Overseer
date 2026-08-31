"""
Overseer SDK — módulos partilhados para todos os pipelines Overseer.

Exporta os componentes principais para importação directa::

    from overseer_sdk import (
        OverseerClient,
        RuntimeContext,
        runtime_ctx,
        SSHTunnelManager,
        get_logger,
        get_log_manager,
        LoggerManager,
        SlackNotifier,
        DatabaseManagerBase,
        DataValidator,
    )
"""

from overseer_sdk.client import OverseerClient
from overseer_sdk.manifest_runner import (
    PipelineManifest,
    ManifestStep,
    load_manifest,
    register_catalog,
    run_manifest,
)
from overseer_sdk.runtime_context import RuntimeContext, runtime_ctx
from overseer_sdk.ssh_tunnel import SSHTunnelManager
from overseer_sdk.logger import LoggerManager, get_log_manager, get_logger
from overseer_sdk.slack_notifier import SlackNotifier
from overseer_sdk.db_manager_base import DatabaseManagerBase
from overseer_sdk.validator import DataValidator

__all__ = [
    "OverseerClient",
    "PipelineManifest",
    "ManifestStep",
    "load_manifest",
    "register_catalog",
    "run_manifest",
    "RuntimeContext",
    "runtime_ctx",
    "SSHTunnelManager",
    "LoggerManager",
    "get_log_manager",
    "get_logger",
    "SlackNotifier",
    "DatabaseManagerBase",
    "DataValidator",
]

__version__ = "5.8.38"
