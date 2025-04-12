import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CodeMirror from "@uiw/react-codemirror";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";

function ApiKeyPage() {
  const [apiKey, setApiKey] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchApiKey = async () => {
      const response = await fetch("/api/api-key");
      if (response.ok) {
        const data = await response.json();
        setApiKey(data.apiKey);
      } else {
        navigate("/");
      }
    };

    fetchApiKey();
  }, [navigate]);

  // const code: string = `- name: Debug with BuildSage Debugging \nif: \${{ failure() || steps.build.outcome == "failure" }}\nuses: ConorJones05/githubactionschatbot@main\nwith:\napi_key: ${apiKey}`;
  const code: string = `- name: Debug with BuildSage Debugging\nif: \${{ failure() || steps.build.outcome == "failure" }}\n\tuses: ConorJones05/githubactionschatbot@main\n\twith:\n\t\tapi_key: test`;
  const code_mirror = <CodeMirror value={code} height="125px" theme={vscodeDark} />;
  
  return (
    <div>
      {apiKey ? <p>{code_mirror}</p> : <p>{code_mirror}</p>}
      <button onClick={() => navigate("/repos")}>View Repositories</button>
    </div>
  );
}

export default ApiKeyPage;