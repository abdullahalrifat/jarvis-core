"""Shared token-efficient agent runtime."""

from .agents import (
    AgentBackend,
    AgentResult,
    SelectiveOrchestrator,
    TaskProfile,
    classify_task,
)
from .artifacts import (
    Artifact,
    ArtifactResolver,
    FileArtifactStore,
    MemoryArtifactStore,
)
from .capabilities import CapabilityRegistry, ModelCapabilities, ModelProfile
from .context import compact_messages, delta_context, summarize_tool_result
from .messages import canonical_message, to_anthropic_messages, to_openai_messages
from .evals import EvalCase, EvalResult, run_evals, score_output
from .recovery import FailureKind, RecoveryDecision, classify_failure
from .search import SearchResult, citation_context, normalize_search_results
from .tracing import TraceEvent, TraceRecorder, redact
from .evidence import (
    Evidence,
    EvidenceLedger,
    EvidenceStatus,
    VerificationStatus,
    VerificationVerdict,
)
from .prompts import PromptRegistry, PromptTemplate, default_prompt_registry
from .tokens import (
    BudgetExceeded,
    TokenBudget,
    TokenLedger,
    TokenReservation,
    Usage,
    estimate_tokens,
)
from .quality import (
    AdaptivePlan,
    ClaimProof,
    CompletionAudit,
    CompletionRequirement,
    EvidenceGate,
    ProofKind,
    QualityMetrics,
    RoleRoute,
    RouteCandidate,
    Scope,
    TaskAnalysis,
    adaptive_plan,
    route_roles,
    stable_cache_key,
)

__all__ = [
    "CapabilityRegistry",
    "ModelCapabilities",
    "ModelProfile",
    "EvalCase",
    "EvalResult",
    "FailureKind",
    "RecoveryDecision",
    "SearchResult",
    "TraceEvent",
    "TraceRecorder",
    "citation_context",
    "classify_failure",
    "normalize_search_results",
    "redact",
    "run_evals",
    "score_output",
    "AgentBackend",
    "AgentResult",
    "Artifact",
    "ArtifactResolver",
    "BudgetExceeded",
    "estimate_tokens",
    "Evidence",
    "EvidenceLedger",
    "EvidenceStatus",
    "FileArtifactStore",
    "MemoryArtifactStore",
    "PromptRegistry",
    "PromptTemplate",
    "SelectiveOrchestrator",
    "TaskProfile",
    "TokenBudget",
    "TokenLedger",
    "TokenReservation",
    "Usage",
    "VerificationStatus",
    "VerificationVerdict",
    "classify_task",
    "canonical_message",
    "compact_messages",
    "to_anthropic_messages",
    "to_openai_messages",
    "default_prompt_registry",
    "delta_context",
    "summarize_tool_result",
    "AdaptivePlan",
    "ClaimProof",
    "CompletionAudit",
    "CompletionRequirement",
    "EvidenceGate",
    "ProofKind",
    "QualityMetrics",
    "RoleRoute",
    "RouteCandidate",
    "Scope",
    "TaskAnalysis",
    "adaptive_plan",
    "route_roles",
    "stable_cache_key",
]

from .benchmarks import BenchmarkObservation, BenchmarkRegistry
from .policy import (
    AttachmentDescriptor,
    Instruction,
    InstructionLevel,
    MCPServerConfig,
    MemoryRecord,
    ToolPermission,
    resolve_instructions,
)
from .resilience import (
    CircuitState,
    IdempotencyLedger,
    ProviderHealth,
    ProviderPool,
)
from .review import ChangeTransaction, ReviewHunk, ReviewState
from .verification import (
    ClaimAssessment,
    SourceAssessment,
    SourceKind,
    rank_sources,
)

__all__ += [
    "AttachmentDescriptor",
    "BenchmarkObservation",
    "BenchmarkRegistry",
    "ChangeTransaction",
    "CircuitState",
    "ClaimAssessment",
    "IdempotencyLedger",
    "Instruction",
    "InstructionLevel",
    "MCPServerConfig",
    "MemoryRecord",
    "ProviderHealth",
    "ProviderPool",
    "ReviewHunk",
    "ReviewState",
    "SourceAssessment",
    "SourceKind",
    "ToolPermission",
    "rank_sources",
    "resolve_instructions",
]
