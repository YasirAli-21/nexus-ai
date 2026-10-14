import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from ai.investigator.llm_investigator import LLMInvestigator


def main():

    evidence = {
        "service": "payment-service",
        "max_cpu": 90.0,
        "max_memory": 88.0,
        "max_latency": 2400.0,
        "max_error_rate": 38.0,
        "error_logs": 50,
        "database_logs": 50,
        "database_messages": {
            "Database connection failed": 10,
            "Database connection timeout": 10,
            "Connection pool exhausted": 10,
            "Unable to acquire database connection": 10,
            "Payment transaction failed due to database error": 10,
        },
    }

    investigator = LLMInvestigator()

    print("\n==============================")
    print("      NEXUS LLM INVESTIGATOR")
    print("==============================")

    analysis = investigator.investigate(evidence)

    print("\n")
    print(analysis)

    print("\n==============================")
    print("       INVESTIGATION DONE")
    print("==============================")


if __name__ == "__main__":
    main()