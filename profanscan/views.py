from django.shortcuts import render
from django.http import JsonResponse
from .profanscan import ProfanScan
from .models import BadWord


def home(request):
    return render(request, 'profanscan/home.html')

def profanscan(request):
    """Retrieve the song title and artist name from the page,
    and perform the ProfanScan on the lyrics (if they can be found).
    Deliver a specific page depending on whether profanity is found or not.

    Parameters
    ----------
    request : HttpRequest
        Metadata from request
    Returns
    -------
    HttpResponse
        Render of a specific HTML page based on the request metadata
    """
    song_title = request.GET.get('song_title')
    artist_name = request.GET.get('artist_name')
    bad_words_qs = BadWord.objects.all()
    bad_words_list = bad_words_qs.values_list('badword', flat=True)

    scan = ProfanScan(song_title=song_title, artist_name=artist_name, bad_words_list=bad_words_list)

    try:
        scan.get_lyrics()
        scan.lyric_scan()
        scan.markup_lyrics()

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

def search_artist(request) -> JsonResponse:
    """Wrapper to deliver the results of search_artist to the page.

    Parameters
    ----------
    request : HttpRequest
        Metadata from request

    Returns
    -------
    JsonResponse
        A JSON filled with the information provided by the python function.
    """
    artist_search_str = request.GET.get("name")
    scan = ProfanScan(artist_name=artist_search_str)
    artist_search_list = scan.search_artists()
    return JsonResponse({'status':200, 'name':artist_search_list})

def search_song(request) -> JsonResponse:
    """Wrapper to deliver the results of search_song or get_song_by_artist to the page.

        Parameters
        ----------
        request : HttpRequest
            Metadata from request

        Returns
        -------
        JsonResponse
            A JSON filled with the information provided by the python function.
        """
    song_search_str = request.GET.get("name")
    artist_name = request.GET.get("artist")
    print(song_search_str)
    print(artist_name)
    if artist_name != 'null':
        scan = ProfanScan(artist_name=artist_name, song_title=song_search_str)
        songs_by_artist = scan.get_songs_by_artist()
        songs_by_artist = [song.replace(u'’', u"'") for song in songs_by_artist]
        print(songs_by_artist)
        return JsonResponse({'status':200, 'name':songs_by_artist})
    else:
        scan = ProfanScan(song_title=song_search_str)
        song_search_list = scan.search_songs()
        return JsonResponse({'status':200, 'name':song_search_list})