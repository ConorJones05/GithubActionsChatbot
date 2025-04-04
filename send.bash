# Ensure logs directory and file exist
        mkdir -p logs
        touch logs/build.log
        
        # Prepare code context data
        CODE_CONTEXT=""
        if [ -d "code_context" ] && [ "$(ls -A code_context 2>/dev/null)" ]; then
          echo "Preparing code context from $(ls code_context | wc -l) files..."
          for snippet in code_context/*; do
            # Add file content with clear separation
            CODE_CONTEXT="${CODE_CONTEXT}===BEGIN_FILE: $(basename "$snippet")===\n$(cat "$snippet")\n===END_FILE===\n\n"
          done
        else
          echo "No code context files found"
        fi
        
        # Escape special characters in logs and code context
        LOGS=$(cat logs/build.log | base64 -w 0)
        CODE_CONTEXT=$(echo "$CODE_CONTEXT" | base64 -w 0)
        
        # Create the request payload
        REQUEST_DATA="{\"api_key\": \"${{ inputs.api_key }}\", \"logs\": \"$LOGS\", \"code_context\": \"$CODE_CONTEXT\", \"encoding\": \"base64\"}"
        
        echo "Sending data to API at ${{ inputs.api_url }}/analyze..."
        RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
          -d "$REQUEST_DATA" \
          "${{ inputs.api_url }}/analyze" 2>&1)
          
        CURL_STATUS=$?
        if [ $CURL_STATUS -ne 0 ]; then
          echo "Error sending data to API: $CURL_STATUS"
          echo "cURL error: $RESPONSE"
        fi

        echo "::group::Here is a method to fix your build"
        echo "$RESPONSE"
        echo "::endgroup::"