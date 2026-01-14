"""
Base agent class for DHCS BHT Multi-Agent System

Updated for BHT Platform integration:
- Phase 1: ALL agents use centralized ModelGateway (no direct provider imports)
- Rollback via BHT_USE_CENTRALIZED_GATEWAY=false changes gateway behavior, not agent code
- Adds trace_id propagation via AuditContext
"""
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from agents.core.config import settings

# Conditional import to avoid circular dependencies
if TYPE_CHECKING:
    from platform.model_gateway import ModelGateway

logger = logging.getLogger(__name__)


def _get_gateway(gateway: Optional["ModelGateway"] = None) -> "ModelGateway":
    """
    Get ModelGateway instance.

    All LLM access MUST go through the gateway - no direct provider imports allowed.
    Rollback behavior is handled inside ModelGateway, not here.
    """
    if gateway is not None:
        return gateway

    from platform.model_gateway import get_default_gateway
    return get_default_gateway()


class BaseAgent:
    """
    Base class for all specialized agents.

    Platform Integration (Phase 1 Hardened):
    - ALL agents use centralized ModelGateway for LLM access
    - No direct ChatOpenAI imports allowed in agents
    - Rollback via BHT_USE_CENTRALIZED_GATEWAY=false changes ModelGateway behavior
    - The `llm` property provides the underlying LLM for chain compatibility
    """

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        gateway: Optional["ModelGateway"] = None,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.model = model or settings.agent_model
        self.temperature = temperature if temperature is not None else settings.agent_temperature

        # ALL agents use gateway - no direct provider access
        self._gateway = _get_gateway(gateway)
        self._llm = self._gateway.get_underlying_llm()
        logger.info(f"Initialized {self.name} agent with ModelGateway (model={self.model})")

    @property
    def llm(self):
        """
        Get the underlying LLM instance.

        This property provides backward compatibility with existing code
        that accesses self.llm directly (e.g., in LangChain chains).
        """
        return self._llm

    @property
    def gateway(self) -> "ModelGateway":
        """
        Get the ModelGateway in use.

        All agents always have a gateway in Phase 1.
        """
        return self._gateway

    def has_gateway(self) -> bool:
        """Check if this agent has a ModelGateway in use. Always True in Phase 1."""
        return True

    def create_prompt(self, system_message: str, human_message: str) -> ChatPromptTemplate:
        """Create a chat prompt template"""
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task
        This method should be overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement execute method")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role})"
