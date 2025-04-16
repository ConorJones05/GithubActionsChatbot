# Standard library imports
import os
import re
import logging
from enum import Enum
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# Third-party imports
import openai
from pydantic import BaseModel, Field, validator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_module")

openai_key = os.environ.get("OPENAI_KEY")
client = openai.OpenAI(api_key=openai_key)


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""
    FIX = "fix"
    NEW_CODE = "new_code"


class LogPacket(BaseModel):
    """Model for log data with file information."""
    logs: str
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('logs')
    def logs_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Logs cannot be empty')
        return v
    
    class Config:
        frozen = True


class GptCompletionConfig(BaseModel):
    """Configuration for OpenAI GPT completion requests."""
    model: str = "gpt-4o"
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    
    class Config:
        frozen = True


class SystemPrompts(BaseModel):
    """Predefined system prompts for different analysis types."""
    fix: str = "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a clear, step-by-step solution. Focus on the actual error shown in the traceback."
    new_code: str = "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a solution for the problem using the code provided. The user should be able to drag and drop the new code into their code and it should work instantly."


class AnalysisResult(BaseModel):
    """Model for the complete analysis result."""
    analysis_type: AnalysisType
    content: str
    log_packet: LogPacket
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def successful(self) -> bool:
        return self.error is None


SYSTEM_PROMPTS = SystemPrompts()


def analyze(logs: str) -> AnalysisResult:
    """Analyze logs and return a GPT-generated fix."""
    logger.info(f"Starting log analysis with {len(logs)} characters of logs")
    parsed_logs = parse_logs(logs)
    result = call_gpt(parsed_logs, AnalysisType.FIX)
    return result


def parse_logs(logs: str) -> LogPacket:
    """Parse logs to extract error details and context."""
    file_pattern = r"===BEGIN_FILE:\s*(.*?)===\n(.*?)===END_FILE==="
    file_match = re.search(file_pattern, logs, re.DOTALL)
    
    file_name = None
    if file_match:
        file_name = file_match.group(1).strip()
        
    return LogPacket(logs=logs, file_name=file_name)


def call_gpt(
    log_packet: LogPacket, 
    analysis_type: AnalysisType, 
    config: Optional[GptCompletionConfig] = None,
    custom_add: Optional[str] = None
) -> AnalysisResult:
    """Call GPT to analyze logs according to the specified analysis type."""
    content = log_packet.logs
    if custom_add:
        content += f"\nAdditional context: {custom_add}"
    
    if config is None:
        config = GptCompletionConfig()
    
    system_prompt = getattr(SYSTEM_PROMPTS, analysis_type.value)
    
    try:
        completion = client.chat.completions.create(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
        )
        
        gpt_response = completion.choices[0].message.content
        
        return AnalysisResult(
            analysis_type=analysis_type,
            content=gpt_response,
            log_packet=log_packet,
            metadata={
                "model": config.model,
                "temperature": config.temperature,
                "finish_reason": completion.choices[0].finish_reason
            }
        )
        
    except Exception as e:
        logger.error(f"Error calling GPT: {str(e)}")
        error_message = f"Failed to analyze logs with GPT: {str(e)}"
        
        return AnalysisResult(
            analysis_type=analysis_type,
            content="",
            log_packet=log_packet,
            error=error_message,
            metadata={"model": config.model}
        )


def call_gpt_fix(
    log_packet: LogPacket, 
    custom_add: Optional[str] = None,
    config: Optional[GptCompletionConfig] = None
) -> str:
    """Call GPT to analyze logs and provide a fix."""
    result = call_gpt(
        log_packet=log_packet,
        analysis_type=AnalysisType.FIX,
        config=config,
        custom_add=custom_add
    )
    
    if result.error:
        raise RuntimeError(result.error)
    
    return result.content


def call_gpt_new_code(
    log_packet: LogPacket, 
    custom_add: Optional[str] = None,
    config: Optional[GptCompletionConfig] = None
) -> str:
    """Call GPT to recommend replacement code."""
    result = call_gpt(
        log_packet=log_packet,
        analysis_type=AnalysisType.NEW_CODE,
        config=config,
        custom_add=custom_add
    )
    
    if result.error:
        raise RuntimeError(result.error)
    
    return result.content