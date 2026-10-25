import csv
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db.session import SessionLocal
from app.models import Wallet


def main() -> None:
    sample_path = Path(__file__).resolve().parents[2] / "data" / "samples" / "flagged_wallets.csv"
    with sample_path.open(encoding="utf-8", newline="") as sample_file:
        wallets = list(csv.DictReader(sample_file))

    with SessionLocal() as session:
        for wallet in wallets:
            statement = sqlite_insert(Wallet).values(
                chain_id=int(wallet["chain_id"]),
                address=wallet["address"].strip().lower(),
                is_flagged=True,
                flag_reason=wallet["flag_reason"].strip(),
            )
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["chain_id", "address"],
                    set_={"is_flagged": True, "flag_reason": wallet["flag_reason"].strip()},
                )
            )
        session.commit()
    print(f"Seeded {len(wallets)} flagged wallets.")


if __name__ == "__main__":
    main()
