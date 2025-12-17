pub struct ThrottleGuard {
    max_bps: u64,
}

impl ThrottleGuard {
    pub fn new(max_bps: u64) -> Self {
        Self { max_bps }
    }

    pub fn clamp(&self, amount: u64) -> u64 {
        let scaled = amount * self.max_bps;
        scaled / 10_000
    }
}
