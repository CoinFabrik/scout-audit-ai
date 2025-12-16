pub mod throttler;

pub use throttler::ThrottleGuard;

pub fn enforce(amount: u64, throttle_bps: u64) -> u64 {
    ThrottleGuard::new(throttle_bps).clamp(amount)
}
