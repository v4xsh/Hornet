import requests
import os
import tqdm
import tarfile

# Tor Expert Bundle URL
url = "https://www.torproject.org/dist/torbrowser/13.0.1/tor-expert-bundle-13.0.1-windows-x86_64.tar.gz"
file_name = "tor-expert-bundle.tar.gz"

# Download Tor Expert Bundle
def download_tor(url, file_name):
    response = requests.get(url, stream=True)
    total = int(response.headers.get('content-length', 0))

    with open(file_name, 'wb') as file, tqdm.tqdm(
        desc=file_name,
        total=total,
        unit='iB',
        unit_scale=True,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

# Extract Tar.gz File
def extract_tar(file_name):
    if file_name.endswith("tar.gz"):
        with tarfile.open(file_name, "r:gz") as tar:
            tar.extractall(".")

# Main Function
def main():
    print("Downloading Tor Expert Bundle...")
    download_tor(url, file_name)
    print("Download complete. Extracting...")
    extract_tar(file_name)
    print("Extraction complete.")

if __name__ == "__main__":
    main()
