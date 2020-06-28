
from .color import Color
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import math
import json
import os
CACHE_DIR = "cache/"
ACH_IDS = "ids.pkl"
CRED_PATH_SPOTIFY = "credentials-spotify.json"
MARKETS = ["FR", "US"]


class Muzik:

    def __init__(self):
        self.ids = self.__read_cache()
        self.spotify = self.__conect_spotify()

    def __read_cache(self) -> pd.Series:
        path = CACHE_DIR + ACH_IDS
        if os.path.exists(path):
            print(f"reading data from cache file {path}")
            df = pd.read_pickle(path)
        else:
            df = pd.Series()
        return df

    def __conect_spotify(self):
        with open(CRED_PATH_SPOTIFY, 'r') as handle:
            data = json.load(handle)
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            **data
        ))

    def __search_strings(self, row):
        """
        Creates the search string for the Spotify API based on
        the information of the row
        Returns a list of multiple strings, to take into account
        if there is special characters (like "'")
        or multiple markets
        input:
            - row : pd.Series with genre, artists, songs,...
        output:
            - searches : list of tuples (search string, market)
        """
        search = ""
        # artists
        artists = list(map(str.strip, row.artist.split(",")))
        if len(artists) > 1:
            sep = '" AND "'
            search += f"artist:\"{sep.join(artists)}\""
        else:
            search += f"artist:\"{artists[0]}\""
        # album
        if row.album != "N/A":
            search += f" album:\"{row.album}\""
        # track name
        search += f" track:\"{row.song}\""
        # dealing with "'""
        # sometimes it will work with the "'" and sometimes not
        if "'" in search:
            searches_s = [search, search.replace("'", "")]
        else:
            searches_s = [search]
        searches = []
        for market in MARKETS:
            for search in searches_s:
                searches.append((search, market))
        return searches

    def __fetch_id(self, df):
        """
        Fetches the Spotify songs id for each provided songs
        If it cannot find ids for a song, it will be set to None
        input:
            - df : a pd.DataFrame with a random index and the
                   song specific columns (genre, artist, ...)
        """
        # small hack to access the data from the index & the columns
        indexs = pd.MultiIndex.from_frame(df)
        songs = pd.DataFrame(data=df.values, index=indexs,
                             columns=df.columns)
        ids = pd.Series(index=indexs,
                        dtype=str, name="ids")
        bad_formats = []
        str_format = int(math.log(len(songs), 10)) + 1
        for idx, (_, content) in enumerate(songs.iterrows()):
            searches = self.__search_strings(content)
            bad_format = []
            for search, market in searches:
                try:
                    res = self.spotify.search(search, market=market)
                    track = res['tracks']['items'][0]
                except IndexError as e:
                    bad_format.append((search, market))
                else:
                    break
            else:
                bad_formats.append(bad_format)
                ids.iloc[idx] = None
                print(f"{Color.FAIL}"
                      f"{idx + 1:<{str_format}}/{len(df)}"
                      f"{Color.ENDC}"
                      f" : {search} not in Spotify")
                continue
            album = track['album']['name']
            name = track['name']
            artist = track['artists'][0]['name']
            id = track['id']
            ids.iloc[idx] = id
            print(f"{Color.OKGREEN}"
                  f"{idx + 1:<{str_format}}/{len(df)}"
                  f"{Color.ENDC}"
                  f" : {id} {name} {artist} {album}")
        return ids

    def update(self, ach):
        """
        updates the known list of ids with the newer version of the
        ach musik sheet
        input:
            - ach : raw sheet from google with multiindex
        """
        # turn the index to DataFrame objects
        new_songs = ach.index.to_frame().reset_index(drop=True)
        old_songs = self.ids.index.to_frame().reset_index(drop=True)
        # get the list of the common values
        common_songs = new_songs.merge(old_songs, how='inner')
        # remove the songs that are not anymore in the cached df
        depr = pd.concat([common_songs, old_songs]).drop_duplicates(keep=False)
        to_remove = pd.MultiIndex.from_frame(depr)
        self.ids = self.ids.drop(to_remove)
        # adds the new songs from the ach sheet
        news = pd.concat([common_songs, new_songs]).drop_duplicates(keep=False)
        new_ids = self.__fetch_id(news)
        self.ids = pd.concat([self.ids, new_ids])
