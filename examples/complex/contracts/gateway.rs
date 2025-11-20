mod adapters;
mod risk;

use adapters::{dex::build_dex_route, lending::build_lending_route};
use risk::throttler::ThrottleGuard;
use crate::math::ratios::basis_points::apply_bps_fee;

pub fn rebalance(amount: u64, throttle_bps: u64) -> u64 {
    let guard = ThrottleGuard::new(throttle_bps);
    let guarded = guard.clamp(amount);

    let dex_quote = build_dex_route(guarded);
    let lending_quote = build_lending_route(guarded);

    apply_bps_fee(dex_quote + lending_quote, 25)
}
