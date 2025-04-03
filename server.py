from fastapi import FastAPI, HTTPException, Request
import debug_module
import vector_logic
import supabase_logic
import uuid
from dotenv import load_dotenv
import re
import base64


load_dotenv()

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "github-actions-chatbot"}

@app.post("/analyze")
async def analyze_logs(request: Request):
    try:
        data = await request.json()
        api_key = data.get("api_key")
        logs = data.get("logs")
        code_context = data.get("code_context", "")
        code_context = base64.b64decode(logs).decode("utf-8")
        if not api_key or not logs:
            print("ERROR: Missing required parameters (api_key or logs)")
            raise HTTPException(status_code=400, detail="Missing required parameters")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    # Validate API key
    if not supabase_logic.check_api_key(api_key=api_key):
        print(f"ERROR: Invalid API key {api_key[:5]}...")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Check if free user has exceeded limits
    # if not supabase_logic.free_user_check(api_key=api_key):
    #     raise HTTPException(status_code=403, detail="Your free trial of BuildSage has ended: Please wait 24 hours or buy a paid plan")

    # Parse logs to extract error information
    try:
        logs_packet, issue = debug_module.parse_logs(logs)
        # Add code context to logs if available
        if code_context:
            if isinstance(logs_packet, tuple):
                logs_packet = (logs_packet[0] + f"\n\nCode context from repository:\n{code_context}", logs_packet[1])
            else:
                logs_packet += f"\n\nCode context from repository:\n{code_context}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing logs: {str(e)}")
    
    # Generate a unique ID for the error
    error_id = str(uuid.uuid4())
    
    # Extract file locations and line numbers to get additional code context
    additional_context = ""
    if issue:
        try:
            file_name, line_number = issue            
        except Exception as e:
            print(f"Error extracting code context: {str(e)}")
        
    # Don't try to access user code locally - it won't be available
    # additional_context += debug_module.access_user_code(file_name, line_number)
    
    # Create vector embedding of the error logs
    try:
        logs_text = logs_packet[0] if isinstance(logs_packet, tuple) else logs_packet
        # Ensure logs don't exceed token limit
        processed_logs = vector_logic.token_checker(logs_text, "cl100k_base")
        error_vector = vector_logic.vector_embeddings(processed_logs)
        
        # Check if this is a similar error to ones seen before
        is_similar = False
        similar_errors = []
        
        # If the user has submitted logs recently, check if it's the same issue
        if supabase_logic.check_last_log(api_key=api_key):
            # Check both direct string matching and vector similarity
            if issue and supabase_logic.error_perfect(api_key=api_key, issue=issue):
                is_similar = True
            else:
                # Predict cluster for the current error
                cluster = vector_logic.predict_vector_cluster(vector=error_vector)
                if cluster is not False:
                    # Find similar errors in the database
                    similar_errors = vector_logic.distance(error_vector)
                    # Consider similar if similarity score is high
                    if similar_errors and any(error['score'] > 0.85 for error in similar_errors):
                        is_similar = True
        
        # If it's a similar error, return a simplified response
        if is_similar:
            return {
                "analysis": "This appears to be the same issue you encountered recently. Please review our previous recommendations.",
                "error_id": error_id,
                "is_duplicate": True
            } #  Maybe fix this to give new repsonce
        
        # Get AI analysis for the error with additional context
        analysis = debug_module.call_GPT_fix((logs_packet, issue), additional_context)
        
        # Store the vector in the database for future reference
        metadata = {
            "genre": "errors",
            "api_key": api_key,
            "issue": str(issue) if issue else "unknown",
            "timestamp": supabase_logic.datetime.now().isoformat()
        }
        vector_logic.add_vector(vector_id=error_id, vector_values=error_vector, metadata=metadata)
        
        # Update user logs
        supabase_logic.update_user_logs(api_key=api_key, issue=issue)
        
        return {
            "analysis": analysis,
            "error_id": error_id,
            "is_duplicate": False,
            "similar_errors": similar_errors[:2] if similar_errors else []
        }
        
    except Exception as e:
        # Fallback to basic analysis if vector processing fails
        try:
            analysis = debug_module.call_GPT_fix(logs_packet, additional_context)
            supabase_logic.update_user_logs(api_key=api_key, issue=issue)
            return {
                "analysis": analysis,
                "error_id": error_id,
                "is_duplicate": False,
                "error_details": str(e)
            }
        except Exception as e2:
            print(f"ERROR in fallback analysis: {str(e2)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e2)}")

