import lyricsgenius
import requests
from musixmatch import Musixmatch
import urllib.parse
import difflib
import re
import os
import yaml
from django.conf import settings

base_dir = settings.BASE_DIR
config_fn = os.path.join(base_dir, str('profanscan/static/profanscan/config.yml'))

with open(config_fn, "r") as f:
    config = yaml.safe_load(f)

musixmatch_token = config['musixmatch_api']['token']

class ProfanScan:
    """
        Class to represent a song that has been scanned for profanity.

        Attributes
        ----------
        artist_name : str
            Artist's name, may be a "substring," as it is populated in real time while the user types
        song_title : str
            Song title, may be a "substring," as it is populated in real time while the user types
        bad_words_list : list
            List of strings that are the bad words being scanned for
        has_bad_word : bool
            Will be switched to True upon bad words being found
        """
    def __init__(self, artist_name=None, song_title=None, bad_words_list=None):
        """All attributes initially set to None, will be quickly updated as user inputs text.
        Initiates the connections to the Deezer and MusixMatch APIs.

        Parameters
        ----------
        artist_name : str
        song_title : str
        bad_words_list : list
        """
        self.artist_name = artist_name
        self.song_title = song_title
        self.bad_words_list = bad_words_list
        self.has_bad_word = False
        self.profan_ids     = []
        self.profan_contexts = []

        self.musixmatch = Musixmatch(musixmatch_token)
        self.deezer_api = "https://api.deezer.com"
        self.chart_api = "http://api.chartlyrics.com/apiv1.asmx"

    def search_artists(self, n_listed: int = 30) -> list:
        """Queries Deezer API to return artist names from a (partial) string search of artist name.

        Parameters
        ----------
        n_listed : int, optional
            Selects how many artists should be listed from the API query (default is 30)

        Returns
        -------
        list
            List of artist names (str) recovered from searching for the currently typed artist name
        """
        search_str_url = urllib.parse.quote(self.artist_name)
        api_search_str = f"search?limit={n_listed}&q={search_str_url}"
        response = requests.get(f"{self.deezer_api}/{api_search_str}")
        search_list = list(set([entry['artist']['name'] for entry in response.json()['data']]))
        search_list = sorted(search_list,
                             key=lambda x: difflib.SequenceMatcher(None, x.lower(), self.artist_name.lower()).ratio(),
                             reverse=True)
        return search_list

    def get_songs_by_artist(self, n_listed: int = 30) -> list:
        """Queries Deezer API to return song titles from a (partial) string search of song titles.
        Different from search_songs in that it also includes artist info in the search.

        Parameters
        ----------
        n_listed : int, optional
            Selects how many songs should be listed from the API query (default is 30)

        Returns
        -------
        list
            List of song titles (str) recovered from searching for the currently typed song title
            and the selected artist
        """
        search_str_url = urllib.parse.quote(f"artist:\"{self.artist_name}\" {self.song_title}")
        print(search_str_url)
        api_search_str = f"search?limit={n_listed}&q={search_str_url}"
        print(api_search_str)
        response = requests.get(f"{self.deezer_api}/{api_search_str}")
        search_list = list(set([entry['title'] for entry in response.json()['data']]))
        song_title_compare = self.song_title.lower() if self.song_title is not None else "".lower()
        search_list = sorted(search_list,
                             key=lambda x: difflib.SequenceMatcher(None, x.lower(), song_title_compare).ratio(),
                             reverse=True)
        print(search_list)

        return search_list

    def search_songs(self, n_listed: int = 30) -> list:
        """Queries Deezer API to return song titles from a (partial) string search of song titles

        Parameters
        ----------
        n_listed : int, optional
            Selects how many songs should be listed from the API query (default is 30)

        Returns
        -------
        list
            List of song titles (str) recovered from searching for the currently typed song title
        """
        search_str_url = urllib.parse.quote(self.song_title)
        api_search_str = f"search?limit={n_listed}&q={search_str_url}"
        response = requests.get(f"{self.deezer_api}/{api_search_str}")
        search_list = list(set([entry['title'] for entry in response.json()['data']]))
        search_list = sorted(search_list,
                             key=lambda x: difflib.SequenceMatcher(None, x.lower(), self.song_title.lower()).ratio(),
                             reverse=True)
        print(search_list)

        return search_list

    def get_lyrics(self) -> str:
        """Searches MusixMatch for lyrics from selected song title and artist name

        Returns
        -------
        str
            Long string of lyrics (includes new line characters)
        """
        mm_lyrics = self.musixmatch.matcher_lyrics_get(self.song_title, self.artist_name)
        self.lyrics = mm_lyrics['message']['body']['lyrics']['lyrics_body']
        self.has_bad_word = mm_lyrics['message']['body']['lyrics']['explicit']
        print(self.has_bad_word)
        self.lyrics = self.lyrics.split("******* This Lyrics is NOT for Commercial use *******")[0]
        print(self.lyrics)
        return self.lyrics

    def lyric_scan(self) -> None:
        """Deprecated function, unused now.
        Scans lyrics for bad words; if any found, adds HTML markup to area surrounding bad word
        """
        strip_lyrics = self.lyrics.replace('\n',' ').split(' ')
        for i, word in enumerate(strip_lyrics):
            for j, badword in enumerate(self.bad_words_list):
                if badword.lower() in word.lower():
                    context = ""
                    start_ind = i - 5 if i - 5 >= 0 else 0
                    end_ind   = i + 6 if i + 6 < len(strip_lyrics) else len(strip_lyrics)
                    for fill_ind in range(start_ind, end_ind):
                        if fill_ind == i:
                            context += "<u><b>"
                        context += strip_lyrics[fill_ind]
                        if fill_ind == i:
                            context += "</b></u>"
                        if fill_ind < end_ind:
                            context += " "
                    self.profan_ids.append(badword)
                    self.profan_contexts.append(context)
                    self.has_bad_word = True

    def markup_lyrics(self) -> None:
        """Scans lyrics for bad words; if any found, adds HTML markup to lyrics string.
        Updates self.lyric_markup with string of marked up lyrics.
        """
        lyric_lines = self.lyrics.split('\n')
        lyric_markup = ""
        for i, line in enumerate(lyric_lines):
            badword_found = False
            for badword in self.bad_words_list:
                if badword.lower() in line.lower():
                    badword_found = True

            if badword_found:
                lyric_markup += "<mark>"

            for j, word in enumerate(line.split(' ')):
                is_badword = False
                end_char = " " if j < len(line.split(" ")) - 1  else ""
                for badword in self.bad_words_list:
                    if badword.lower() in word.lower():
                        is_badword = True
                if is_badword:
                    lyric_markup += "<u><b>"

                lyric_markup += word

                if is_badword:
                    lyric_markup += "</u></b>"
                lyric_markup += end_char

            if badword_found:
                lyric_markup += "</mark>"

            lyric_markup += "<br />\n"

        self.lyric_markup = lyric_markup