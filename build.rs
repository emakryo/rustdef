use std::process::Command;

fn main() {
    Command::new("rm").arg("package.zip").spawn();
    Command::new("zip")
        .args(&["-r", "package.zip", "Cargo.toml", "src"])
        .spawn()
        .expect("failed to zip");
}