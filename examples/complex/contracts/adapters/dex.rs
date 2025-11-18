use crate::math::ratios::basis_points::apply_bps_fee;

pub fn build_dex_route(amount: u64) -> u64 {
    let adjusted = apply_bps_fee(amount, 80);
    adjusted / 2
}
