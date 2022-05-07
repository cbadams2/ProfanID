import lyricsgenius
import re

client_id = "iEuxCOVRaLMDuocugCaJ-de6WK4n-CWQpMEC6eRsqAr-WXNGVOMZ1uqsqDqT3K9f"
client_secret = "O3e6kRICrYQPocj-hG_uCq9WapilQN9X3Yu_D1Zh7RO0NtLl6wwS6nwuUubpOYnYoSum6gxai69HWRDtTbXrCQ"
client_access_token = "4I3BgkfVa9PxIQLYus67euEQq_hXCsaylIT0QmRK7EL2E00HOA7HvJHHtwWdyvWU"

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

    def get_lyrics(self):
        song = self.genius.search_song(self.song_title, self.artist_name)
        self.lyrics = song.lyrics
        return song.lyrics

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