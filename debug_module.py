import os
import re
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai


def analyze(logs):
    return call_GPT_fix(parse_logs(logs))
    

def parse_logs(logs):
    logs_packet = f"Here are the logs {logs}. Here is the code for where the errors are occuring"

    file_line_pattern = r'File "([^"]+)", line (\d+)' #  Checks for Start with "set of chars"

    traceback_pattern = r'File "([^"]+)", line (\d+), in (\S+)' #  Checks for Start with "set of chars" and String without white spaces

    file_line_matches = re.findall(file_line_pattern, logs)

    traceback_matches = re.findall(traceback_pattern, logs)

    # SyntaxError
    if file_line_matches:
        for match in file_line_matches:
            file_name, line_number = match
            logs_packet += access_user_code(file_name, line_number)
    else:
        print("No file or line number found.")

    # Traceback
    if traceback_matches:
        for match in traceback_matches:
            file_name, line_number, function_name = match
            logs_packet += access_user_code(file_name, line_number, function_name) #  could build on function name later
    else:
        print("No traceback information found.")

    result = logs_packet
    issue = file_line_matches[0] if file_line_matches else None
    
    return result, issue


def access_user_code(file_name, line_number, function_name=None):
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()
            start = max(0, int(line_number) - 3)
            end = min(len(lines), int(line_number) + 3)
            code_context = ''.join(lines[start:end])
            
            function_detail = f" in function '{function_name}'" if function_name else ""
            return f"\nCode context for {file_name} around line {line_number}{function_detail}:\n{code_context}"
    except FileNotFoundError:
        return f"\nCould not find file: {file_name}\n"
    except Exception as e:
        return f"\nError accessing code: {str(e)}\n"
    

def call_GPT_fix(logs_packet, custom_add = None):
    logs_text, issue = logs_packet
    content = logs_text
    if custom_add:
        content += f"\nAdditional context: {custom_add}"
        
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "system",
        "content": "You are an agent in charge of helping people fix their broken builds. Analyze these logs and code to identify the error and provide a clear, step-by-step solution."
    }, {
        "role": "user",
        "content": content}])
    return completion.choices[0].message