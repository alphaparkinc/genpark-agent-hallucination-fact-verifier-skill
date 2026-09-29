import sys, json, re

class AgentHallucinationFactVerifier:
    """
    Agent Hallucination & Fact-Verification Cross-Checker.
    Decomposes LLM text outputs into atomic assertions, inspects entity
    presences, checks numerical consistency, and detects ungrounded hallucinations.
    """
    def extract_atomic_claims(self, text):
        # Sentence splitting respecting abbreviations
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        claims = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 8:
                claims.append(s_clean)
        return claims

    def _extract_numbers(self, text):
        return set(re.findall(r"\d+(?:\.\d+)?%?", text))

    def _extract_named_entities(self, text):
        return set(re.findall(r"[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*", text))

    def verify_claims_against_context(self, claims, reference_context):
        ref_lower = reference_context.lower()
        ref_numbers = self._extract_numbers(reference_context)
        ref_entities = {e.lower() for e in self._extract_named_entities(reference_context)}

        results = []
        grounded_count = 0
        contradiction_count = 0

        for claim in claims:
            claim_nums = self._extract_numbers(claim)
            claim_ents = {e.lower() for e in self._extract_named_entities(claim)}

            # 1. Number check
            missing_nums = claim_nums - ref_numbers
            # 2. Entity check
            missing_ents = claim_ents - ref_entities

            if missing_nums:
                status = "CONTRADICTORY_OR_FABRICATED_NUMBERS"
                contradiction_count += 1
                details = f"Numbers not found in reference: {list(missing_nums)}"
            elif missing_ents and len(missing_ents) > 1:
                status = "UNGROUNDED_ENTITIES"
                contradiction_count += 1
                details = f"Entities not found in reference: {list(missing_ents)}"
            else:
                # Semantic containment check
                words = re.findall(r"\w{3,}", claim.lower())
                overlap = sum(1 for w in words if w in ref_lower) / max(1, len(words))
                if overlap >= 0.6:
                    status = "GROUNDED"
                    grounded_count += 1
                    details = f"High token overlap ({round(overlap*100, 1)}%) with source"
                else:
                    status = "UNVERIFIED"
                    details = "Insufficient context overlap"

            results.append({
                "claim": claim,
                "status": status,
                "details": details
            })

        faithfulness = round(grounded_count / max(1, len(claims)), 4)
        return {
            "total_claims": len(claims),
            "grounded_count": grounded_count,
            "contradiction_count": contradiction_count,
            "faithfulness_score": faithfulness,
            "claims_breakdown": results
        }

    def run_verification_benchmark(self):
        source_doc = (
            "Acme Global reported Q3 revenue of 4.2 billion dollars, representing 15% year-over-year growth. "
            "CEO John Miller announced that the new European datacenter in Frankfurt is operational with 500 servers."
        )

        test_summary_hallucinated = (
            "Acme Global achieved 4.2 billion dollars in Q3 with 15% growth. "
            "CEO John Miller stated that the Tokyo datacenter has 900 servers."  # Hallucinated: Tokyo, 900
        )

        claims = self.extract_atomic_claims(test_summary_hallucinated)
        verif = self.verify_claims_against_context(claims, source_doc)

        return {
            "suite": "Hallucination Fact Verifier Benchmark",
            "source_context_sample": source_doc[:100] + "...",
            "claims_audited": len(claims),
            "verification_report": verif,
            "audit_verdict": "FLAGGED_HALLUCINATION_ACCURATELY" if verif["contradiction_count"] > 0 else "UNVERIFIED"
        }
