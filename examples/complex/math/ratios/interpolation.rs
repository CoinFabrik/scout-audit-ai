pub fn weighted_average(a: u64, b: u64, weight_a: u64) -> u64 {
    let weight_b = 100 - weight_a;
    ((a * weight_a) + (b * weight_b)) / 100
}
