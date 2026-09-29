from client import AgentHallucinationFactVerifier
import json

verifier = AgentHallucinationFactVerifier()
print("=== AGENT HALLUCINATION FACT VERIFIER BENCHMARK ===")
res = verifier.run_verification_benchmark()
print(json.dumps(res, indent=2))
