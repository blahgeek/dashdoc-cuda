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
        "--reject='*.pdf'",
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


# All the docs are linked here: https://docs.nvidia.com/cuda/
# But downloading all of them takes way too long, so I just made a sensible
# Selection
URLS = [
    "https://docs.nvidia.com/cuda/parallel-thread-execution/index.html",
    "https://docs.nvidia.com/cuda/cublas/index.html",
    "https://docs.nvidia.com/cuda/cuda-runtime-api/index.html",
    "https://docs.nvidia.com/cuda/cuda-math-api/index.html",
    "https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html",
    "https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/",
    "https://docs.nvidia.com/cuda/ampere-tuning-guide/index.html",
    "https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html",
    "https://docs.nvidia.com/cuda/ada-tuning-guide/index.html",
    "https://docs.nvidia.com/cuda/cuda-driver-api/index.html",
    "https://docs.nvidia.com/cuda/cusparse/index.html",
    "https://docs.nvidia.com/cuda/nvjpeg/index.html",
    "https://docs.nvidia.com/cuda/cufft/index.html",
    "https://docs.nvidia.com/cuda/curand/index.html",
    "https://docs.nvidia.com/cuda/cusolver/index.html",
]
BASE_DIR = Path(__file__).parent / "docs.nvidia.com"

if __name__ == "__main__":
    for url in URLS:
        name = url.split("/")[-2]
        if not (BASE_DIR / "cuda" / name).exists():
            download_website(url)
