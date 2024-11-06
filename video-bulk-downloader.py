import os
import requests
import argparse
from tqdm import tqdm

def sanitize_filename(name):
    """Sanitize the filename by removing or replacing invalid characters."""
    return name.replace(" ", "_").replace("'", "").replace('"', "")

def download_video(title, url, download_folder):
    """Download a video from the given URL."""
    filename = f"{sanitize_filename(title)}.mp4"
    filepath = os.path.join(download_folder, filename)

    # Check if the file already exists
    if os.path.exists(filepath):
        existing_size = os.path.getsize(filepath)
        print(f"'{title}' already exists with size {existing_size / (1024 * 1024):.2f} MB.")

        # Get the file size from the server to determine if a resume is possible
        response = requests.head(url)
        total_size = int(response.headers.get('content-length', 0))

        # Check if the existing file is already complete
        if existing_size >= total_size:
            print(f"'{title}' is already fully downloaded. Skipping download.")
            return False  # Indicate that download was skipped

        # If not complete, set the starting point for the download
        headers = {'Range': f'bytes={existing_size}-'}
    else:
        existing_size = 0
        headers = {}

    try:
        # Start downloading with the appropriate headers
        response = requests.get(url, stream=True, headers=headers, timeout=10)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0)) if 'content-length' in response.headers else None

        with open(filepath, "ab") as file:  # Open file in append mode
            with tqdm(total=total_size, initial=existing_size, unit='B', unit_scale=True, desc=title) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        pbar.update(len(chunk))

        print(f"'{title}' downloaded successfully to '{filepath}'.")
        return True  # Indicate that download was successful

    except requests.exceptions.RequestException as e:
        print(f"Failed to download '{title}': {e}")
        return False  # Indicate that download failed
    except Exception as e:
        print(f"Unexpected error while downloading '{title}': {e}")
        return False  # Indicate that download failed

def read_video_links(file_path):
    """Read video links from a specified file."""
    videos = []
    try:
        with open(file_path, "r") as file:
            for line in file:
                if " - " in line:
                    title, url = line.strip().split(" - ", 1)
                    videos.append((title, url))
        return videos
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Video Downloader CLI")
    parser.add_argument('file', help="Path to the text file containing video links (Title - URL format)")
    parser.add_argument('-d', '--download_folder', default=os.getcwd(), help="Folder to save downloaded videos")
    
    args = parser.parse_args()

    videos = read_video_links(args.file)

    if not videos:
        print("No videos found to download.")
        return

    # Download videos one by one and print messages accordingly
    for title, url in videos:
        download_video(title, url, args.download_folder)
        print("\n")  # Add a newline for better readability between downloads

if __name__ == "__main__":
    main()
