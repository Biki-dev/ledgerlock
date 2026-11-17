from database import Base, engine

import models


def migrate_phase5(target_engine=engine):
	Base.metadata.create_all(bind=target_engine)


if __name__ == "__main__":
	migrate_phase5()
	print("Phase 5 assurance table created.")