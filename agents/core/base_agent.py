"""
Base agent class for DHCS BHT Multi-Agent System
"""
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough

from agents.core.config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all specialized agents"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.model = model or settings.agent_model
        self.temperature = temperature or settings.agent_temperature

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            openai_api_key=settings.openai_api_key
        )

        logger.info(f"Initialized {self.name} agent with model {self.model}")

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
