from src.database import SessionLocal
from src.models import Claim


def main():
    db = SessionLocal()

    claims = db.query(Claim).limit(10).all()

    print("=" * 60)
    print("FIRST 10 CLAIMS IN DATABASE")
    print("=" * 60)

    for claim in claims:
        print(
            f"ID: {claim.claim_id} | "
            f"Customer: {claim.customer_id} | "
            f"Status: {claim.status}"
        )

    db.close()


if __name__ == "__main__":
    main()