import lyricsgenius
import re
import os
import yaml
from django.conf import settings

base_dir = settings.BASE_DIR
config_fn = os.path.join(base_dir, str('profanscan/static/profanscan/config.yml'))

with open(config_fn, "r") as f:
    config = yaml.safe_load(f)

client_id           = config['genius_api']['client_id']
client_secret       = config['genius_api']['client_secret']
client_access_token = config['genius_api']['client_access_token']

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

        self.genius = lyricsgenius.Genius(client_access_token)

    def search_artists(self, **kwargs):
        artist_dict = self.genius.search_artists(self.artist_name, **kwargs)
        search_list = []
        for i in range(len(artist_dict['sections'][0]['hits'])):
            artist_hit = artist_dict['sections'][0]['hits'][i]['result']['name']
            print(artist_hit)
            search_list.append(artist_hit)
        return search_list

    def get_songs_by_artist(self, **kwargs):
        artist = self.genius.search_artist(self.artist_name, max_songs=0, **kwargs)
        dict = {}
        page = 1
        songs = []
        while page:
            print(page*50)
            request = self.genius.artist_songs(artist.id,
                                               sort='popularity',
                                               per_page=50,
                                               page=page,
                                               )
            songs.extend(request['songs'])
            page=request['next_page']

        song_list = []
        for i in range(len(songs)):
            song_list.append(songs[i]['title'])
        print(song_list)

        return song_list

    def search_songs(self, **kwargs):
        song_dict = self.genius.search_songs(self.song_title, **kwargs)
        song_search_list = []
        for i in range(len(song_dict['hits'])):
            song_hit = song_dict['hits'][i]['result']['title']
            song_search_list.append(song_hit)
        print(song_search_list)

        return song_search_list




    def get_lyrics(self):
        self.song = self.genius.search_song(self.song_title, self.artist_name)
        self.lyrics = self.song.lyrics
        return self.song.lyrics

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
        lyric_markup = "<h3>"
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

                if i == 0 and 'lyrics[' in word.lower():
                    split_beginning = word.split("[")
                    lyric_markup += f"{split_beginning[0]}\n</h3><br />"
                    lyric_markup += f"[{split_beginning[1]}"
                elif i == len(lyric_lines)-1 and 'embed' in word.lower():
                    lyric_markup += re.sub(r'(.*?)(?:\d*)?(?:E|e)mbed', r'\1', word)
                else:
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