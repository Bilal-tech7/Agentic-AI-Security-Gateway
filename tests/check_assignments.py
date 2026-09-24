from src.database import SessionLocal
from src.models import ClaimAssignment, User


def main():

    db = SessionLocal()

    print("=" * 60)
    print("CLAIM ASSIGNMENT CHECK")
    print("=" * 60)

    assignments = (
        db.query(ClaimAssignment)
        .limit(10)
        .all()
    )

    for assignment in assignments:

        user = (
            db.query(User)
            .filter(
                User.user_id == assignment.user_id
            )
            .first()
        )

        print(
            f"Claim: {assignment.claim_id} | "
            f"User: {assignment.user_id} | "
            f"Role: {user.role if user else 'UNKNOWN'} | "
            f"Active: {assignment.active}"
        )

    print()
    print(f"Assignments found: {len(assignments)}")

    db.close()


if __name__ == "__main__":
    main()
