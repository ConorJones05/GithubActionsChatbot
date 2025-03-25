import os
import re
import openai

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai

def analyze(logs):
    return call_GPT_fix(parse_logs(logs))


def parse_logs(logs):
    logs_packet = f"Here are the logs {logs}. Here is the code for where the errors are occuring"

    file_line_pattern = r'File "([^"]+)", line (\d+)'

    traceback_pattern = r'File "([^"]+)", line (\d+), in (\S+)'

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

    return logs_packet


def access_user_code(file_name, line_number, function_name=None):
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()
            start = max(0, int(line_number) - 3)
            end = min(len(lines), int(line_number) + 3)
            return ''.join(lines[start:end]), lines[int(line_number) - 1].strip()
    except FileNotFoundError:
        return f"Could not find file: {file_name}", ""
    

def call_GPT_fix(logs_packet):
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "system",
        "content": "You are an agent incharge of helping people fix there broken builds look these logs and code and find the error"
    }, {
        "role": "user",
        "content": logs_packet}])
    return completion.choices[0].message 


