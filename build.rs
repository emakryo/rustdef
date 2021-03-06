use glob::glob;
use std::fs;
use std::io::Error;
use std::io::{copy, Seek, Write};
use std::path::Path;
use zip::{write::FileOptions, ZipWriter};

fn recursive<W: Write + Seek>(writer: &mut ZipWriter<W>, dir: &Path) -> Result<(), Error> {
    writer
        .add_directory(dir.to_string_lossy(), FileOptions::default())
        .map_err(Error::from)?;
    for ent in fs::read_dir(dir)? {
        let path = ent.map_err(Error::from)?.path();
        if path.is_dir() {
            recursive(writer, &path)?;
        } else if path.is_file() {
            writer
                .start_file(path.to_string_lossy(), FileOptions::default())
                .map_err(Error::from)?;
            let mut f = fs::File::open(path)?;
            copy(&mut f, writer)?;
        }
    }
    Ok(())
}

fn main() {
    let src_files = glob("src/**/*.rs").expect("failed to glob src");
    for f in src_files {
        let path = f.expect("failed to get path");
        println!("cargo::rerun-if-changed={}", path.display());
    }
    println!("cargo::rerun-if-changed=Cargo.toml");
    let filename = "package.zip";
    let mut writer = fs::File::create(filename).expect("failed to create");
    let mut writer = ZipWriter::new(&mut writer);

    let filename = Path::new("Cargo.toml");
    writer
        .start_file(filename.to_string_lossy(), FileOptions::default())
        .expect("failed to add to zip");
    let mut f = fs::File::open(filename).expect("failed to create");
    copy(&mut f, &mut writer).expect("failed to copy");

    recursive(&mut writer, Path::new("src")).expect("failed to add src");

    writer.finish().expect("failed to write zip");
}
