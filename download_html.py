import subprocess
from pathlib import Path


def download_website(url):
    print(f"Downloading website: {url}")
    command = [
        "wget",
        "--recursive",
        "--no-clobber",
        "--page-requisites",
        "--html-extension",
        "--convert-links",
        "--restrict-file-names=windows",
        "--domains",
        "docs.nvidia.com",
        "--no-parent",
        url,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Website downloaded successfully: {url}")
    except subprocess.CalledProcessError as error:
        print(f"Error downloading website: {url}. Error: {error}")


URLS = [
    "https://docs.nvidia.com/cuda/parallel-thread-execution/index.html",
    "https://docs.nvidia.com/cuda/cublas/index.html",
]
BASE_DIR = Path(__file__) / "docs.nvidia.com"

if __name__ == "__main__":
    for url in URLS:
        name = url.split("/")[-2]
        if not (BASE_DIR / name).exists():
            download_website(url)
