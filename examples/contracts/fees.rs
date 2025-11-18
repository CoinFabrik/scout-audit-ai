pub fn apply_basis_points_fee(amount: u64, bps: u64) -> u64 {
    if bps == 0 || amount == 0 {
        return amount;
    }

    let fee = amount.saturating_mul(bps) / 10_000;
    amount.saturating_sub(fee)
}
