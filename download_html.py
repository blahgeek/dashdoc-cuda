import subprocess


def download_website(url):
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


if __name__ == "__main__":
    url = "https://docs.nvidia.com/cuda/cublas/index.html"
    download_website(url)
