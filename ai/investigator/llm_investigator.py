from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config.settings import OPENAI_API_KEY

from ai.investigator.investigator import AIInvestigator


class LLMInvestigator:

    def __init__(self):

        self.fallback = AIInvestigator()

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=0,
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are NEXUS, an AI production incident investigator.

Analyze ONLY the evidence provided.

Do not invent facts.

Clearly distinguish observed evidence from hypotheses.

Return your response using EXACTLY this structure:

ROOT CAUSE:
<probable root cause>

EVIDENCE:
- <observed evidence>
- <observed evidence>

CONFIDENCE:
HIGH

RECOMMENDED ACTIONS:
- <action>
- <action>

CONFIDENCE must be exactly one of:
HIGH
MEDIUM
LOW
"""
            ),
            (
                "human",
                """
Investigate this production incident.

Service:
{service}

Maximum CPU:
{max_cpu}%

Maximum Memory:
{max_memory}%

Maximum Latency:
{max_latency} ms

Maximum Error Rate:
{max_error_rate}%

Error Logs:
{error_logs}

Database Logs:
{database_logs}

Database Messages:
{database_messages}
"""
            ),
        ])

    def _parse_response(self, response_text):

        text = response_text.strip()

        root_cause = ""
        evidence = []
        confidence = "LOW"
        recommendations = []

        sections = {
            "ROOT CAUSE:": "root_cause",
            "EVIDENCE:": "evidence",
            "CONFIDENCE:": "confidence",
            "RECOMMENDED ACTIONS:": "recommendations",
        }

        current_section = None

        for raw_line in text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            upper_line = line.upper()

            if upper_line == "ROOT CAUSE:":
                current_section = "root_cause"
                continue

            if upper_line == "EVIDENCE:":
                current_section = "evidence"
                continue

            if upper_line == "CONFIDENCE:":
                current_section = "confidence"
                continue

            if upper_line == "RECOMMENDED ACTIONS:":
                current_section = "recommendations"
                continue

            if current_section == "root_cause":

                if not root_cause:
                    root_cause = line

            elif current_section == "evidence":

                if line.startswith("-"):
                    evidence.append(line[1:].strip())
                else:
                    evidence.append(line)

            elif current_section == "confidence":

                value = line.upper()

                if value in {"HIGH", "MEDIUM", "LOW"}:
                    confidence = value

            elif current_section == "recommendations":

                if line.startswith("-"):
                    recommendations.append(line[1:].strip())
                else:
                    recommendations.append(line)

        return {
            "root_cause": root_cause,
            "evidence": evidence,
            "confidence": confidence,
            "recommendations": recommendations,
        }

    def investigate(self, evidence: dict):

        try:

            chain = self.prompt | self.llm

            response = chain.invoke({
                "service": evidence["service"],
                "max_cpu": evidence["max_cpu"],
                "max_memory": evidence["max_memory"],
                "max_latency": evidence["max_latency"],
                "max_error_rate": evidence["max_error_rate"],
                "error_logs": evidence["error_logs"],
                "database_logs": evidence["database_logs"],
                "database_messages": evidence["database_messages"],
            })

            parsed = self._parse_response(response.content)

            return {
                "investigation_mode": "LLM",
                "root_cause": parsed["root_cause"],
                "evidence": parsed["evidence"],
                "confidence": parsed["confidence"],
                "recommendations": parsed["recommendations"],
                "analysis": response.content,
            }

        except Exception as error:

            print("\n⚠️ LLM unavailable.")
            print(f"Reason: {error}")
            print("Switching to deterministic investigation...\n")

            return self.fallback.investigate(evidence)