import sys, json
from client import AgentHallucinationFactVerifier

def handle_mcp():
    verifier = AgentHallucinationFactVerifier()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(json.dumps(verifier.run_verification_benchmark(), indent=2))
        return

    for line in sys.stdin:
        if not line.strip(): continue
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")
            
            if method == "initialize":
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "genpark-agent-hallucination-fact-verifier-skill", "version": "1.0.0"},
                    "capabilities": {"tools": {}}
                }}
            elif method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": [
                    {"name": "extract_atomic_claims", "description": "Decompose text into atomic claims.", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}},
                    {"name": "verify_claims_against_context", "description": "Verify claims against reference source context.", "inputSchema": {"type": "object", "properties": {"claims": {"type": "array"}, "reference_context": {"type": "string"}}}},
                    {"name": "run_verification_benchmark", "description": "Run fact verification benchmark.", "inputSchema": {"type": "object"}}
                ]}}
            elif method == "tools/call":
                tname = req.get("params", {}).get("name")
                args = req.get("params", {}).get("arguments", {})
                if tname == "extract_atomic_claims":
                    res = verifier.extract_atomic_claims(args.get("text", ""))
                elif tname == "verify_claims_against_context":
                    res = verifier.verify_claims_against_context(args.get("claims", []), args.get("reference_context", ""))
                else:
                    res = verifier.run_verification_benchmark()
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}
            
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}}) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    handle_mcp()
