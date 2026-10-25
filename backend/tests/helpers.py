def csv_payload(*rows: str) -> str:
    return (
        "chain_id,tx_hash,from_address,to_address,amount,asset_symbol,timestamp,status,block_number\n"
        + "\n".join(rows)
    )
