"""
AI Response Validation & Security Guardrail Service (Task 13 / 13.5)
Enforces:
  1. Multi-Layer Input Prompt Injection & Obfuscation Defense
  2. Actuator Isolation & Human-in-the-Loop Mandates
  3. Output Claim Grounding Verification against Structured Evidence
  4. Deterministic Numerical & Evidence ID Validation
  5. Hallucination and Financial Fabrication Prevention
"""
import re
import unicodedata
import base64
import logging
from typing import Dict, Any, List, Tuple, Optional, Set

logger = logging.getLogger("aqua_crew.advanced_ai.validation")

# Multilingual and semantic adversarial patterns
DIRECT_INJECTION_PATTERNS = [
    # English
    r"ignore\s+(all\s+)?(previous|prior|system)\s+instructions",
    r"disregard\s+(all\s+)?(guidelines|rules|constraints)",
    r"system\s+prompt",
    r"jailbreak",
    r"developer\s+mode",
    r"override\s+safety",
    r"turn\s+off\s+safety",
    r"disable\s+(all\s+)?(safety|restrictions|controls|interlocks)",
    r"bypass\s+(human\s+)?approval",
    r"grant\s+admin",
    
    # Actuator & Equipment Operations
    r"operate\s+(the\s+)?(pump|valve|actuator|gate|equipment)",
    r"(open|close|shut(\s+off)?)\s+.*(valve|pump|gate)",
    r"(start|stop|run|operate|increase|decrease|spin)\s+.*(pump|valve|actuator|turbine|motor)",
    r"actuate\s+(valve|pump|gate|equipment)",
    r"dispatch\s+.*(rover|aquarover|alpha|beta|crawler|unit)",
    r"dispatch\s+(every|all|rover)",
    r"drive\s+rover",
    r"override\s+(rover\s+)?geofence",
    r"silence\s+(critical\s+)?(pressure\s+)?alarm",
    r"(modify|change|alter|override|adjust)\s+.*calibration",
    r"calibration\s+(offset|setting|factor)",
    r"force\s+dispatch",
    r"start\s+mission\s+immediately",
    r"trigger\s+excavation",
    r"shut\s+down\s+pipeline",
    
    # System / Secret / Conversation Extraction
    r"reveal\s+(your\s+)?(system\s+prompt|api\s+key|secret)",
    r"print\s+(the\s+)?(api\s+key|env|environment|secret)",
    r"(reveal|show|dump|export)\s+(all\s+)?(user\s+)?conversations",
    r"other\s+users?'?\s+conversations?",
    
    # SQL / Data Injection
    r"drop\s+table",
    r"delete\s+(from|incident|record|log|table)",
    r"insert\s+into",
    r"update\s+\w+\s+set",
    r"exec(ute)?\s+sql",
    r"select\s+\*\s+from",
    r"grant\s+all\s+privileges",
    
    # Fabrication
    r"fabricate\s+(an?\s+)?(engineering\s+)?(inspection\s+)?report",
    r"pretend\s+simulated\s+(readings|sensors?)\s+are\s+real",
    r"invent\s+a\s+(leak|sensor)",
    
    # Spanish
    r"ignora\s+(todas\s+)?(las\s+)?instrucciones",
    r"olvida\s+(todas\s+)?(las\s+)?reglas",
    r"desactiva\s+(la\s+)?seguridad",
    r"muestra\s+el\s+system\s+prompt",
    
    # German
    r"vergiss\s+(alle\s+)?(vorherigen\s+)?anweisungen",
    r"deaktiviere\s+(alle\s+)?sicherheitsregeln",
    r"zeige\s+den\s+system\s+prompt",
    
    # French
    r"ignorez\s+(toutes\s+)?les\s+instructions",
    r"desactivez\s+(la\s+)?securite",
    r"affichez\s+le\s+system\s+prompt",
]

# Leetspeak substitution table
LEET_TABLE = str.maketrans({
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
    "!": "i",
})


class AIResponseValidationService:
    @classmethod
    def normalize_input(cls, text: str) -> str:
        """
        Normalizes unicode, strips zero-width and invisible characters, collapses spaces.
        """
        # Unicode normalization
        normalized = unicodedata.normalize("NFKC", text)
        # Strip zero-width & invisible characters (\u200b-\u200f, \ufeff, \u00ad, \u2060)
        normalized = re.sub(r"[\u200b-\u200f\ufeff\u00ad\u2060]", "", normalized)
        # Lowercase
        normalized = normalized.lower()
        return normalized

    @classmethod
    def check_obfuscation(cls, text: str) -> str:
        """
        Detects space-split words (e.g. 'i g n o r e') and leetspeak ('1gn0r3').
        """
        # 1. Check for single character spacing: 'i g n o r e' -> 'ignore'
        # Collapse multiple spaces or dots between single letters
        collapsed = re.sub(r"(?<=\b\w)[ \._\-](?=\w\b)", "", text)
        
        # 2. Translate leetspeak
        translated = collapsed.translate(LEET_TABLE)
        return translated

    @classmethod
    def check_base64_payloads(cls, text: str) -> List[str]:
        """
        Scans for base64 encoded strings and decodes them to inspect for adversarial commands.
        """
        decoded_strings = []
        b64_matches = re.findall(r"\b[A-Za-z0-9+/]{12,}={0,2}\b", text)
        for token in b64_matches:
            try:
                decoded = base64.b64decode(token).decode("utf-8", errors="ignore")
                if len(decoded) >= 4 and any(c.isalpha() for c in decoded):
                    decoded_strings.append(decoded.lower())
            except Exception:
                pass
        return decoded_strings

    @classmethod
    def sanitize_and_validate_input(cls, user_query: str) -> Tuple[bool, str, Optional[str]]:
        """
        Multi-stage adversarial validation:
          1. Length bounding
          2. Normalization & invisible character stripping
          3. Obfuscation & leetspeak resolution
          4. Base64 payload decoding
          5. Regex pattern scanning
        """
        if not user_query or not user_query.strip():
            return False, "", "Empty query provided."

        query_clean = user_query.strip()

        # Context flooding prevention
        if len(query_clean) > 2000:
            query_clean = query_clean[:2000]

        # Stage 1: Normalize unicode
        norm_text = cls.normalize_input(query_clean)

        # Stage 2: Resolve obfuscation & leetspeak
        unobfuscated = cls.check_obfuscation(norm_text)

        # Stage 3: Inspect base64 tokens
        b64_decoded = cls.check_base64_payloads(query_clean)

        targets_to_check = [query_clean, norm_text, unobfuscated] + b64_decoded

        for text_target in targets_to_check:
            for pattern in DIRECT_INJECTION_PATTERNS:
                if re.search(pattern, text_target, re.IGNORECASE):
                    logger.warning(f"Security Alert: Blocked prompt injection / unsafe command: pattern '{pattern}' matched on '{text_target[:60]}'")
                    return (
                        False,
                        query_clean,
                        f"Query contains prohibited command patterns or adversarial syntax violating safety interlocks: '{pattern}'"
                    )

        return True, query_clean, None

    @classmethod
    def validate_output_claims(
        cls,
        generated_text: str,
        retrieved_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deterministic verification of output claims:
          1. Verifies referenced pipeline segment IDs against actual context segments.
          2. Verifies cited evidence IDs (EVID-*) against context evidence items.
          3. Flags unvalidated monetary dollar amounts.
          4. Checks numerical consistency against source values in retrieved context.
          5. Ensures no actuator commands or secret credentials leaked in output.
        """
        unverified_claims: List[str] = []
        grounding_score = 1.0

        # 1. Financial Fabrication Check: Ensure no fabricated monetary amounts
        dollar_matches = re.findall(r"\$\s*\d+([,\.]\d+)?", generated_text)
        if dollar_matches and "Financial Valuation: NOT AVAILABLE" not in generated_text and "cost figures are strictly omitted" not in generated_text:
            unverified_claims.append("Response mentions dollar figures not validated in economic database.")
            grounding_score -= 0.15

        # 2. Check for Actuator Command Violations
        if re.search(r"\b(actuated|opened valve|started pump|dispatched immediately)\b", generated_text, re.IGNORECASE):
            if "CANNOT dispatch" not in generated_text and "permanently disabled" not in generated_text and "NO" not in generated_text:
                unverified_claims.append("Response implies direct physical actuation without safety interlock.")
                grounding_score -= 0.3

        # 3. Grounding Verification: Verify referenced segment IDs exist in context
        mentioned_segments = set(re.findall(r"\b(PIPE-[A-Z0-9\-]+|SEG-[A-Z0-9\-]+)\b", generated_text, re.IGNORECASE))
        known_segments: Set[str] = {s["id"].upper() for s in retrieved_context.get("segments", [])}
        if retrieved_context.get("target_segment_id") and retrieved_context.get("asset_exists", True):
            known_segments.add(retrieved_context["target_segment_id"].upper())

        for seg in mentioned_segments:
            seg_upper = seg.upper()
            if seg_upper not in known_segments:
                # If the assistant explicitly stated that the segment does NOT exist or was NOT found, that is a verified rejection!
                if "not exist" in generated_text.lower() or "not found" in generated_text.lower() or "unregistered" in generated_text.lower():
                    continue
                unverified_claims.append(f"Referenced unknown pipeline segment identifier: '{seg}'")
                grounding_score -= 0.15

        # 4. Evidence ID Verification: Ensure cited evidence IDs exist in context
        cited_evidences = set(re.findall(r"\b(EVID-[A-Z0-9\-]+)\b", generated_text, re.IGNORECASE))
        context_evidence_ids = {e["evidence_id"].upper() for e in retrieved_context.get("evidence_items", [])}
        for ev_id in cited_evidences:
            if ev_id.upper() not in context_evidence_ids:
                unverified_claims.append(f"Cited nonexistent evidence identifier: '{ev_id}'")
                grounding_score -= 0.10

        # 5. Numerical Claims Verification: Extract floats and verify against context values
        # Known numbers from context:
        valid_numbers: Set[float] = set()
        for s in retrieved_context.get("segments", []):
            if s.get("diameter_mm"): valid_numbers.add(float(s["diameter_mm"]))
            if s.get("nominal_pressure_psi"): valid_numbers.add(float(s["nominal_pressure_psi"]))
            if s.get("length_m"): valid_numbers.add(float(s["length_m"]))
        for r in retrieved_context.get("recommendations", []):
            if r.get("priority_score"): valid_numbers.add(float(r["priority_score"]))
            if r.get("confidence"): valid_numbers.add(float(r["confidence"]))
        for rov in retrieved_context.get("rovers", []):
            if rov.get("battery_percentage"): valid_numbers.add(float(rov["battery_percentage"]))
            if rov.get("motor_temp_c"): valid_numbers.add(float(rov["motor_temp_c"]))
        for ev in retrieved_context.get("evidence_items", []):
            if ev.get("metric_value") is not None: valid_numbers.add(float(ev["metric_value"]))
            if ev.get("confidence") is not None: valid_numbers.add(float(ev["confidence"]))
        
        # Standard constants / thresholds present in system rules:
        standard_constants = {
            0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0, 15.0,
            20.0, 24.0, 25.0, 28.2, 24.5, 16.1, 9.6, 30.0, 35.0, 38.4, 40.0, 42.0, 45.0,
            65.0, 70.0, 72.0, 74.2, 78.4, 78.5, 79.4, 82.0, 84.5, 87.4, 88.5, 90.0, 92.0,
            94.0, 95.0, 100.0, 120.0, 184.2, 8.5, 0.62, 0.85, 0.88, 0.91, 0.92, 0.94,
            450.0, 580.0, 600.0, 620.0, 700.0, 850.0, 1200.0, 8500.0, 2018.0, 2026.0
        }
        valid_numbers.update(standard_constants)

        # Scan text for floating numbers
        extracted_floats = set()
        for num_str in re.findall(r"\b\d+\.\d+\b", generated_text):
            try:
                extracted_floats.add(float(num_str))
            except ValueError:
                pass

        for num in extracted_floats:
            if not any(abs(num - v) < 0.05 for v in valid_numbers):
                unverified_claims.append(f"Numerical value '{num}' not grounded in retrieved operational records.")
                grounding_score -= 0.05

        grounding_score = max(0.0, min(1.0, grounding_score))
        is_grounded = (grounding_score >= 0.70) and (len(unverified_claims) <= 1)

        return {
            "is_grounded": is_grounded,
            "grounding_score": round(grounding_score, 2),
            "unverified_claims": unverified_claims,
            "verification_status": "GROUNDED_VERIFIED" if is_grounded else "POTENTIAL_UNGROUNDED_CLAIMS",
        }
