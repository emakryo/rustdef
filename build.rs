use std::process::Command;

fn main() {
    Command::new("rm")
        .args(&["-f", "package.zip"])
        .spawn()
        .expect("failed to rm");
    Command::new("zip")
        .args(&["-r", "package.zip", "Cargo.toml", "src"])
        .spawn()
        .expect("failed to zip");
}