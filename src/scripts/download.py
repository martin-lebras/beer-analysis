import gdown
import subprocess
import os
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <raw data path>")
    sys.exit(1)

PATH = sys.argv[1]
SAFE_MODE = False
DATASETS = [
    (
        "BeerAdvocate.tar.gz",
        "1IqcAJtYrDB1j40rBY5M-PGp6KNX-E3xq",
        "beer_advocate",
        [("ratings.txt.gz", "ratings.txt"), ("reviews.txt.gz", "reviews.txt")],
    ),
    (
        "matched_beer_data.tar.gz",
        "1SdScOOuA219GeA6jP6CTkj98FP_X0DMe",
        "matched_beer_data",
        [
            ("ratings_ba.txt.gz", "ratings_ba.txt"),
            ("ratings_rb.txt.gz", "ratings_rb.txt"),
            ("ratings_with_text_ba.txt.gz", "ratings_with_text_ba.txt"),
            ("ratings_with_text_rb.txt.gz", "ratings_with_text_rb.txt"),
        ],
    ),
    (
        "RateBeer.tar.gz",
        "1vt-CTz6Ni8fPTIkHehW9Mm0RPMpvkH3a",
        "rate_beer",
        [("ratings.txt.gz", "ratings.txt"), ("reviews.txt.gz", "reviews.txt")],
    ),
]

os.makedirs(PATH, exist_ok=True)

for filename, google_drive_id, folder, additional_files in DATASETS:
    os.makedirs(os.path.join(PATH, folder), exist_ok=True)
    file_path = os.path.join(PATH, folder, filename)

    gdown.download(id=google_drive_id, output=file_path, quiet=False)
    subprocess.run(["tar", "-xf", file_path, "-C", os.path.join(PATH, folder)])

    if not SAFE_MODE:
        subprocess.run(["rm", file_path])
    else:
        print(f"[*] You can delete {file_path}")

    for input_file, output_file in additional_files:
        with open(os.path.join(PATH, folder, output_file), "wb") as file_object:
            subprocess.run(
                ["gzip", "-dc", os.path.join(PATH, folder, input_file)],
                stdout=file_object,
            )

        if not SAFE_MODE:
            subprocess.run(["rm", os.path.join(PATH, folder, input_file)])
        else:
            print(f"[*] You can delete {os.path.join(PATH, folder, input_file)}")
