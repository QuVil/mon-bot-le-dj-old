import contributor
import track

def initialize() -> tuple:
    tracks, ratings = [], []
    for row in list(data()):
        current_track = track(row[0], row[1], row[2], row[3], row[4])
        tracks.append(current_track)
        ratings.append((current_track, [as_real_or_none(row[5 + contributor[0]]) for contributor in CONTRIBUTORS]))
    return (tracks, ratings)

def condorcet_method(candidate):
    pass

def schulze_method():
    pass


tracks, ratings = initialize()
for rating in list(ratings):
    print(rating)
