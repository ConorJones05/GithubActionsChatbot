import os
import re
import openai
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, Tuple

load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai


class LogPacket(BaseModel):
    logs: str
    file_name: Optional[str] = None
    line_number: Optional[int] = None


def analyze(logs: str) -> str:
    """Analyze logs and return a GPT-generated fix."""
    print(f"Starting log analysis with {len(logs)} characters of logs")
    parsed_logs = parse_logs(logs)
    return call_gpt_fix(parsed_logs)


def parse_logs(logs: str) -> LogPacket:
    """Parse logs to extract error details and context."""
    logs_packet = f"Here are the logs:\n{logs}"
    file_line_pattern = r'File "([^"]+)", line (\d+)'
    traceback_pattern = r'File "([^"]+)", line (\d+), in (\S+)'

    traceback_matches = re.findall(traceback_pattern, logs)
    file_line_matches = re.findall(file_line_pattern, logs)

    if traceback_matches:
        file_name, line_number, _ = traceback_matches[-1]
        return LogPacket(logs=logs_packet, file_name=file_name, line_number=int(line_number))
    elif file_line_matches:
        file_name, line_number = file_line_matches[-1]
        return LogPacket(logs=logs_packet, file_name=file_name, line_number=int(line_number))

    return LogPacket(logs=logs_packet)


def call_gpt_fix(log_packet: LogPacket, custom_add: Optional[str] = None) -> str:
    """Call GPT to analyze logs and provide a fix."""
    content = log_packet.logs
    if custom_add:
        content += f"\nAdditional context: {custom_add}"

    try:
        completion = client.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a clear, step-by-step solution. Focus on the actual error shown in the traceback.",
                },
                {"role": "user", "content": content},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Failed to analyze logs with GPT: {str(e)}")
    
def call_gpt_new_code(log_packet: LogPacket, custom_add: Optional[str] = None) -> str:
    """Call GPT give recommendations about the code to switch out."""
    content = log_packet.logs
    if custom_add:
        content += f"\nAdditional context: {custom_add}"

    try:
        completion = client.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a solution for the probelm using the code provided. THe user should be able to drag and drop the new code inot there code and it work instantly.",
                },
                {"role": "user", "content": content},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Failed to analyze for new code with GPT: {str(e)}")