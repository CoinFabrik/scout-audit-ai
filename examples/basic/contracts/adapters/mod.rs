pub mod dex;
pub mod lending;

pub use dex::build_dex_route;
pub use lending::build_lending_route;

pub fn summarize_routes(amount: u64) -> u64 {
    build_dex_route(amount) + build_lending_route(amount)
}
