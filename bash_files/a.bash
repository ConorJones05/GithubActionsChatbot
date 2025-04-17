mkdir -p code_context
        echo "Starting code context extraction..."
        
        # Extract file paths and line numbers from logs
        grep -E 'File "([^"]+)", line [0-9]+|([^:]+):[0-9]+:[0-9]+:|Error in [^:]+:[0-9]+' logs/build.log || echo "No pattern found in logs"
        
        grep -E 'File "([^"]+)", line [0-9]+|([^:]+):[0-9]+:[0-9]+:|Error in [^:]+:[0-9]+' logs/build.log | while read -r match; do
          echo "Processing match: $match"
          
          # Try different patterns to extract file path and line number
          if [[ "$match" =~ File\ \"([^\"]+)\",\ line\ ([0-9]+) ]]; then
            file_path="${BASH_REMATCH[1]}"
            line_num="${BASH_REMATCH[2]}"
          elif [[ "$match" =~ ([^:\ ]+):([0-9]+):[0-9]+: ]]; then
            file_path="${BASH_REMATCH[1]}"
            line_num="${BASH_REMATCH[2]}"
          elif [[ "$match" =~ Error\ in\ ([^:]+):([0-9]+) ]]; then
            file_path="${BASH_REMATCH[1]}"
            line_num="${BASH_REMATCH[2]}"
          else
            # Fall back to original pattern
            file_path=$(echo "$match" | grep -o 'File "[^"]*"' | sed 's/File "//;s/"$//')
            line_num=$(echo "$match" | grep -o 'line [0-9]*' | sed 's/line //')
          fi
          
          echo "Found reference to file: $file_path at line: $line_num"
          
          # Check if the file exists
          if [ -f "$file_path" ]; then
            echo "File exists at exact path, extracting context..."
            # Extract context (5 lines before and after the error line)
            start_line=$((line_num - 5))
            if [ $start_line -lt 1 ]; then 
              start_line=1
            fi
            end_line=$((line_num + 5))
            
            snippet_name=$(echo "$file_path" | sed 's/[\/\\:]/_/g')
            echo "FILE: $file_path, LINE: $line_num" > "code_context/${snippet_name}_${line_num}.txt"
            sed -n "${start_line},${end_line}p" "$file_path" >> "code_context/${snippet_name}_${line_num}.txt"
            echo "Context extracted to code_context/${snippet_name}_${line_num}.txt"
          else
            echo "File not found at $file_path, searching in repository..."
            base_name=$(basename "$file_path")
            potential_file=$(find . -type f -name "$base_name" | head -1)
            
            if [ -n "$potential_file" ] && [ -f "$potential_file" ]; then
              echo "Found potential match: $potential_file"
              start_line=$((line_num - 5))
              if [ $start_line -lt 1 ]; then 
                start_line=1
              fi
              end_line=$((line_num + 5))
              
              snippet_name=$(echo "$potential_file" | sed 's/[\/\\:]/_/g')
              echo "FILE: $potential_file, LINE: $line_num" > "code_context/${snippet_name}_${line_num}.txt"
              sed -n "${start_line},${end_line}p" "$potential_file" >> "code_context/${snippet_name}_${line_num}.txt"
              echo "Context extracted from potential match"
            else
              echo "Warning: Could not find file '$file_path' or any matching files"
            fi
          fi
        done || echo "No matching files found in logs"
        
        # List extracted context files
        echo "Extracted code context files:"
        ls -la code_context/ || echo "No context files were created"