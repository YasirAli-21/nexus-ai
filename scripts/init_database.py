import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.core.database import Base, engine

from backend.app.models.incident import Incident
from backend.app.models.evidence import Evidence
from backend.app.models.timeline import TimelineEvent


def main():

    print("Initializing NEXUS database...")

    Base.metadata.create_all(
        bind=engine
    )

    print("Database initialized successfully.")


if __name__ == "__main__":
    main()