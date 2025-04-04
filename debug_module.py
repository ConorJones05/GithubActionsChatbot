import os
import re
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai


def analyze(logs):
    print(f"Starting log analysis with {len(logs)} characters of logs")
    return call_GPT_fix(parse_logs(logs))
    

def parse_logs(logs):
    logs_packet = f"Here are the logs:\n{logs}"

    file_line_pattern = r'File "([^"]+)", line (\d+)'

    traceback_pattern = r'File "([^"]+)", line (\d+), in (\S+)'

    file_line_matches = re.findall(file_line_pattern, logs)

    traceback_matches = re.findall(traceback_pattern, logs)
    
    if traceback_matches:
        # Identify the error location
        file_name, line_number, function_name = traceback_matches[-1]  # Use the deepest frame in the traceback
        return (logs_packet, (file_name, line_number))
    elif file_line_matches:
        # Identify the error location, but don't try to access the file
        file_name, line_number = file_line_matches[-1]  # Use the last file reference
        return (logs_packet, (file_name, line_number))
    
    return (logs_packet, None)

# def access_user_code(file_name, line_number, function_name=None):
#     print(f"Attempting to access code in {file_name} at line {line_number}")
#     try:
#         with open(file_name, 'r') as file:
#             lines = file.readlines()
#             start = max(0, int(line_number) - 3)
#             end = min(len(lines), int(line_number) + 3)
#             code_context = ''.join(lines[start:end])
            
#             function_detail = f" in function '{function_name}'" if function_name else ""
#             print(f"Successfully extracted {end-start} lines of context around line {line_number}")
#             return f"\nCode context for {file_name} around line {line_number}{function_detail}:\n{code_context}"
#     except FileNotFoundError:
#         print(f"WARNING: File not found: {file_name} (this is expected for test files)")
#         # Return empty string without mentioning the file couldn't be found
#         return ""
#     except Exception as e:
#         print(f"ERROR accessing code: {str(e)}")
#         return ""
    

def call_GPT_fix(logs_packet, custom_add = None):
    logs_text = logs_packet[0]
    print(logs_text)
    content = logs_text
    
    if custom_add:
        content += f"\nAdditional context: {custom_add}"
    
    completion = client.ChatCompletion.create(
    model="gpt-4o",
    messages=[{
        "role": "system",
        "content": "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a clear, step-by-step solution. Focus on the actual error shown in the traceback."
    }, {
        "role": "user",
        "content": content}])
    return completion.choices[0].message