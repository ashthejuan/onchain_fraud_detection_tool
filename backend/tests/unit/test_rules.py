from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Transaction, Wallet
from app.rules.v1 import assess_transaction


def _session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False)()


def _tx(session: Session, **kwargs: object) -> Transaction:
    count = session.scalar(select(func.count()).select_from(Transaction)) or 0
    defaults: dict[str, object] = {
        "chain_id": 1,
        "tx_hash": f"0x{count + 1:064x}",
        "from_address": "0xfrom",
        "to_address": "0xto",
        "amount": Decimal("1"),
        "asset_symbol": "ETH",
        "block_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "status": "success",
        "block_number": count + 1,
    }
    defaults.update(kwargs)
    row = Transaction(**defaults)
    session.add(row)
    session.flush()
    return row


def test_large_transfer_threshold_and_severity_bands() -> None:
    session = _session()
    low = assess_transaction(session, _tx(session, tx_hash="0xl1", amount=Decimal("99.99")))
    mid = assess_transaction(session, _tx(session, tx_hash="0xl2", amount=Decimal("100")))
    assert low.risk_score == 0 and low.severity == "low"
    assert mid.risk_score == 25 and mid.severity == "medium"
    assert [r["rule_id"] for r in mid.triggered_rules] == ["large_transfer"]


def test_velocity_requires_five_successes_inside_window() -> None:
    session = _session()
    base = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    for index in range(3):
        _tx(session, tx_hash=f"0xv{index}", from_address="0xvel", block_timestamp=base + timedelta(minutes=index))
    just_under = assess_transaction(
        session,
        _tx(session, tx_hash="0xv3", from_address="0xvel", block_timestamp=base + timedelta(minutes=9)),
    )
    assert just_under.risk_score == 0

    fifth = assess_transaction(
        session,
        _tx(session, tx_hash="0xv4", from_address="0xvel", block_timestamp=base + timedelta(minutes=9, seconds=30)),
    )
    assert "high_velocity" in [r["rule_id"] for r in fifth.triggered_rules]

    outside = assess_transaction(
        session,
        _tx(session, tx_hash="0xv5", from_address="0xvel", block_timestamp=base + timedelta(minutes=20)),
    )
    assert "high_velocity" not in [r["rule_id"] for r in outside.triggered_rules]


def test_rapid_movement_requires_prior_inbound_within_30_minutes() -> None:
    session = _session()
    receive_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    _tx(session, tx_hash="0xrecv", from_address="0xsrc", to_address="0xmid", block_timestamp=receive_at)
    inside = assess_transaction(
        session,
        _tx(
            session,
            tx_hash="0xfwd",
            from_address="0xmid",
            to_address="0xdst",
            block_timestamp=receive_at + timedelta(minutes=29),
        ),
    )
    assert "rapid_fund_movement" in [r["rule_id"] for r in inside.triggered_rules]

    outside = assess_transaction(
        session,
        _tx(
            session,
            tx_hash="0xfwd2",
            from_address="0xmid",
            to_address="0xdst",
            block_timestamp=receive_at + timedelta(minutes=31),
        ),
    )
    assert "rapid_fund_movement" not in [r["rule_id"] for r in outside.triggered_rules]


def test_repeated_failures_window_and_flagged_exposure_cap() -> None:
    session = _session()
    session.add(Wallet(chain_id=1, address="0xflag", is_flagged=True, flag_reason="demo"))
    session.flush()
    base = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    for index in range(2):
        _tx(
            session,
            tx_hash=f"0xf{index}",
            from_address="0xfail",
            status="failed",
            block_timestamp=base + timedelta(minutes=index),
        )
    third = assess_transaction(
        session,
        _tx(
            session,
            tx_hash="0xf2",
            from_address="0xfail",
            status="failed",
            block_timestamp=base + timedelta(minutes=2),
        ),
    )
    assert third.risk_score == 15 and third.severity == "low"

    capped = assess_transaction(
        session,
        _tx(
            session,
            tx_hash="0xcap",
            from_address="0xflag",
            to_address="0xto",
            amount=Decimal("500"),
            block_timestamp=base,
        ),
    )
    assert capped.risk_score == 65
    assert capped.severity == "high"
    assert {r["rule_id"] for r in capped.triggered_rules} == {"large_transfer", "flagged_wallet_exposure"}
