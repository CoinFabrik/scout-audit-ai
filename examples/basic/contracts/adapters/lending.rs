use crate::math::ratios::basis_points::apply_bps_fee;
use crate::math::ratios::interpolation::weighted_average;

pub fn build_lending_route(amount: u64) -> u64 {
    let conservative = apply_bps_fee(amount, 20);
    let aggressive = apply_bps_fee(amount, 5);
    weighted_average(conservative, aggressive, 60)
}
