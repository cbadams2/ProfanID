from django.shortcuts import render
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
        if song_title.lower() not in scan.song.title.lower().strip():
            raise Exception

        if len(scan.profan_ids) > 0:
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