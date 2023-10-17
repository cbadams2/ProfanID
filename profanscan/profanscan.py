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

# client_id           = config['genius_api']['client_id']
# client_secret       = config['genius_api']['client_secret']
# client_access_token = config['genius_api']['client_access_token']

musixmatch_token = config['musixmatch_api']['token']

# genius = lyricsgenius.Genius(client_access_token)
#
# artist_name = "Ariana Grande"
# song_title = "Positions"
#
# song = genius.search_song(song_title, artist_name)
# print(song.title)
# print(song.lyrics)

class ProfanScan:
    def __init__(self, artist_name=None, song_title=None, bad_words_list=None):
        self.artist_name = artist_name
        self.song_title = song_title
        self.bad_words_list = bad_words_list
        self.has_bad_word = False
        self.profan_ids     = []
        self.profan_contexts = []

        # self.genius = lyricsgenius.Genius(client_access_token)
        self.musixmatch = Musixmatch(musixmatch_token)
        self.deezer_api = "https://api.deezer.com"
        self.chart_api = "http://api.chartlyrics.com/apiv1.asmx"

    def search_artists(self, n_listed = 30):
        search_str_url = urllib.parse.quote(self.artist_name)
        api_search_str = f"search?limit={n_listed}&q={search_str_url}"
        response = requests.get(f"{self.deezer_api}/{api_search_str}")
        search_list = list(set([entry['artist']['name'] for entry in response.json()['data']]))
        search_list = sorted(search_list,
                             key=lambda x: difflib.SequenceMatcher(None, x.lower(), self.artist_name.lower()).ratio(),
                             reverse=True)
        return search_list

    def get_songs_by_artist(self, n_listed=30):
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
        # artist = self.genius.search_artist(self.artist_name, max_songs=0, **kwargs)
        # dict = {}
        # page = 1
        # songs = []
        # while page:
        #     print(page*50)
        #     request = self.genius.artist_songs(artist.id,
        #                                        sort='popularity',
        #                                        per_page=50,
        #                                        page=page,
        #                                        )
        #     songs.extend(request['songs'])
        #     page=request['next_page']
        #
        # song_list = []
        # for i in range(len(songs)):
        #     song_list.append(songs[i]['title'])
        # print(song_list)

        return search_list

    def search_songs(self, n_listed=30):
        search_str_url = urllib.parse.quote(self.song_title)
        api_search_str = f"search?limit={n_listed}&q={search_str_url}"
        response = requests.get(f"{self.deezer_api}/{api_search_str}")
        search_list = list(set([entry['title'] for entry in response.json()['data']]))
        search_list = sorted(search_list,
                             key=lambda x: difflib.SequenceMatcher(None, x.lower(), self.song_title.lower()).ratio(),
                             reverse=True)
        print(search_list)
        # song_dict = self.genius.search_songs(self.song_title, **kwargs)
        # song_search_list = []
        # for i in range(len(song_dict['hits'])):
        #     song_hit = song_dict['hits'][i]['result']['title']
        #     song_search_list.append(song_hit)
        # print(song_search_list)

        return search_list




    def get_lyrics(self):
        # self.song = self.genius.search_song(self.song_title, self.artist_name)
        # self.lyrics = self.song.lyrics
        mm_lyrics = self.musixmatch.matcher_lyrics_get(self.song_title, self.artist_name)
        self.lyrics = mm_lyrics['message']['body']['lyrics']['lyrics_body']
        self.has_bad_word = mm_lyrics['message']['body']['lyrics']['explicit']
        print(self.has_bad_word)
        # search_str_url = f"artist={urllib.parse.quote(self.artist_name)}&song={urllib.parse.quote(self.song_title)}"
        # api_search_str = f"SearchLyricDirect?{search_str_url}"
        # request_url = f"{self.chart_api}/{api_search_str}"
        # print(request_url)
        # response = requests.get(request_url)
        # print(response)
        print(self.lyrics)
        return self.lyrics

    def lyric_scan(self):
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

    def markup_lyrics(self):
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

# scan = ProfanScan(song_title=song_title, artist_name=artist_name, bad_words_list=["shit","fuck"])
# scan.get_lyrics()
# scan.lyric_scan()
# print(scan.lyrics)