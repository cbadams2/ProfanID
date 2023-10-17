from django.shortcuts import render
from django.http import JsonResponse
from .profanscan import ProfanScan
from .models import BadWord


def home(request):
    return render(request, 'profanscan/home.html')

def profanscan(request):
    song_title = request.GET.get('song_title')
    artist_name = request.GET.get('artist_name')
    bad_words_qs = BadWord.objects.all()
    bad_words_list = bad_words_qs.values_list('badword', flat=True)

    scan = ProfanScan(song_title=song_title, artist_name=artist_name, bad_words_list=bad_words_list)

    try:
        scan.get_lyrics()
        scan.lyric_scan()
        scan.markup_lyrics()

        # meant to avoid issues where the API provides the wrong result
        # test case: Shaking Ass by Jerry Paper
        # if song_title.lower() not in scan.song.title.lower().strip():
        #     raise Exception

        if scan.has_bad_word:
            profan_zip = zip(scan.profan_ids, scan.profan_contexts)
            return render(request,
                          'profanscan/scan.html',
                          {
                              'scan_result': profan_zip,
                              'artist_name': artist_name,
                              'song_title': song_title,
                              'lyric_markup': scan.lyric_markup,
                          },
            )
        else:
            web_lyrics = scan.lyrics.replace("\n","<br />\n")
            return render(request,
                          'profanscan/nocuss.html',
                          {
                              'lyrics': web_lyrics,
                              'artist_name': artist_name,
                              'song_title': song_title,
                          }
                          )
    except Exception as e:
        print(e)
        return render(request,
                      'profanscan/notfound.html',
                      {
                          'artist_name': artist_name,
                          'song_title': song_title,
                      }
                      )

def search_artist(request):
    artist_search_str = request.GET.get("name")
    scan = ProfanScan(artist_name=artist_search_str)
    artist_search_list = scan.search_artists()
    return JsonResponse({'status':200, 'name':artist_search_list})

def search_song(request):
    print("yello!!!")
    song_search_str = request.GET.get("name")
    artist_name = request.GET.get("artist")
    print(song_search_str)
    print(artist_name)
    if artist_name != 'null':
        print('entered if')
        scan = ProfanScan(artist_name=artist_name, song_title=song_search_str)
        songs_by_artist = scan.get_songs_by_artist()
        songs_by_artist = [song.replace(u'’', u"'") for song in songs_by_artist]
        print(songs_by_artist)
        return JsonResponse({'status':200, 'name':songs_by_artist})
    else:
        print('entered else')
        scan = ProfanScan(song_title=song_search_str)
        song_search_list = scan.search_songs()
        return JsonResponse({'status':200, 'name':song_search_list})
