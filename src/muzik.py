
from .color import Color
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import math
import json
import hashlib
import os
CACHE_DIR = "cache/"
ACH_IDS = "ids.pkl"
CRED_PATH_SPOTIFY = "credentials-spotify.json"
MARKETS = ["FR", "US"]


class Muzik:

    def __init__(self, public_api=False):
        self.__create_cache_dir()
        self.ids = self.__read_cached_ids()
        if public_api:
            self.sp = self.__connect_spotify()
        self.sp_user = self.__connect_spotify_user()

    def __create_cache_dir(self):
        """
        Create cache dir at `CACHE_DIR` if doesn't already exists    
        """
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

    def __read_cached_ids(self) -> pd.Series:
        """
        Read the cached already fetched ids from the cache folder
        either returns the cached pd.Series, or empty series if
        no file there
        """
        path = CACHE_DIR + ACH_IDS
        if os.path.exists(path):
            print(f"reading data from cache file {path}")
            df = pd.read_pickle(path)
        else:
            df = pd.Series()
        return df

    def __read_credentials(self):
        """
        Opens and return the content of `CRED_PATH_SPOTIFY` as
        a python dict
        """
        with open(CRED_PATH_SPOTIFY, 'r') as handle:
            data = json.load(handle)
        return data

    def __connect_spotify_user(self):
        """
        Connect to the API using the spotify user credentials
        needs more informations than the other method, but can
        access to personnal informations (including playlists :o)
        of the user
        """
        data = self.__read_credentials()
        # generate a unique random number to prevent csrf
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        self.__user_credentials = SpotifyOAuth(
            **data,
            state=state,
        )
        return spotipy.Spotify(
            auth=self.__user_credentials.get_access_token(as_dict=False)
        )

    def __connect_spotify(self):
        """
        Connect to the public API of Spotify, useful to fetch songs ids
        since the API limite rate is higher here, however not really
        useful to create playlists and stuff
        """
        data = self.__read_credentials()
        auth = {}
        auth["client_id"] = data["client_id"]
        auth["client_secret"] = data["client_secret"]
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            **auth
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
