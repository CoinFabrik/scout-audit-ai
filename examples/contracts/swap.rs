mod fees;

use fees::apply_basis_points_fee;

pub fn swap(amount_in: u64, pool_balance: u64) -> u64 {
    if pool_balance == 0 {
        return 0;
    }

    // TODO: replace with proper invariant check
    let amount_after_fee = apply_basis_points_fee(amount_in, 100);
    let output = amount_after_fee.min(pool_balance);
    output
}
