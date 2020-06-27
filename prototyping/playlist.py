import random

import pandas as pd
from data import load_from_api, load_from_cache

KEPT_PEOPLE = ["Qu", "Gr", "Vi", "Ro"]
DEFAULT_GRADE = 5
COUNT_FACTOR = .1
COUNT_INHIB = len(KEPT_PEOPLE) // 2
MIN_SCORE = 5
PLAYLIST_SIZE = 300  # Can be an int or a fraction 0 < q <= 1 of the songs


def create_playlist():
    print("Loading data from API...")
    data = load_from_api()

    # Getting the decimals right -- commas to points and no more Nones
    print("Analyzing data...")
    data = data.set_index(["genre", "sub_genre", "artist", "album", "song"])
    data.fillna(value="", inplace=True)

    for i in range(data.columns.size):
        data[data.columns[i]] = data[data.columns[i]].str.replace(",", ".")
        data[data.columns[i]] = pd.to_numeric(data[data.columns[i]], errors='coerce')

    # Keeping only present people at the hypothetical party!
    data = data.filter(KEPT_PEOPLE)

    # Hard to do this shit inplace -- if no grades at all, give it a chance to play with default grade
    data = data.dropna(how="all").append(data[data.isnull().all(axis=1)].fillna(DEFAULT_GRADE))

    # Mean of all notes for each track
    data["mean"] = data[data.columns].mean(axis=1)
    # Amount of notes for each track
    data["count"] = data.count(axis=1) - 1
    # Helping songs graded by more people in the group
    data["score"] = data["mean"] + (COUNT_FACTOR * (data["count"] - COUNT_INHIB))
    # Truncating to keep only the acceptable songs
    data = data[data["score"] > MIN_SCORE]

    # Using ranking of scores as weight for the playlist bootstrap
    print("Creating playlist...")
    data = data.sort_values("score", ascending=False)
    data["rank"] = data["score"].rank(method="min")

    if PLAYLIST_SIZE < 1:
        playlist = data.sample(frac=PLAYLIST_SIZE, weights="rank")
    else:
        playlist = data.sample(n=PLAYLIST_SIZE, weights="rank")

    # Rearranging playlist to avoid sudden genre changes
    genres = [playlist for _, playlist in playlist.groupby("genre")]
    random.shuffle(genres)

    return pd.concat(genres)


if __name__ == "__main__":
    print(create_playlist())
