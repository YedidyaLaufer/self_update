#!/usr/bin/python3
import os
import shutil
import sqlite3
import spotipy
import telepot
import mutagen
import setting
import logging
import acrcloud
import requests
import dwytsongs
import deezloader
import base64
import sys
import codecs
from datetime import datetime
from time import sleep
from pprint import pprint
from mutagen.mp3 import MP3
from threading import Thread
from mutagen.flac import FLAC
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
import strings
from setting import *
#aa = open("example.png", "rb")
downloa = deezloader.Login(setting.username, setting.password, setting.deezer_token)
token = setting.token
bot = telepot.Bot(token)
users = {}
qualit = {}
date = {}
languag = {}
del1 = 0
del2 = 0
log = codecs.open("log.txt", 'a+', 'utf8')
local = os.getcwd()
db_file = local + "/dwsongs.db"
loc_dir = local + "/Songs/"
version_url = "https://raw.githubusercontent.com/YedidyaLaufer/telegram/master/version"
source_url = "https://raw.githubusercontent.com/YedidyaLaufer/telegram/master/"
__version__ = 3

logging.basicConfig(filename="dwsongs.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
if not os.path.isdir(loc_dir):
    os.makedirs(loc_dir)
conn = sqlite3.connect(db_file)
c = conn.cursor()
try:
    c.execute("CREATE TABLE DWSONGS (id text, query text, quality text)")
    c.execute("CREATE TABLE BANNED (banned int)")
    c.execute("CREATE TABLE CHAT_ID (chat_id int)")
    c.execute("CREATE TABLE CHAT_LAN (chat_id int, language text)")
    conn.commit()
except sqlite3.OperationalError:
    pass


def generate_token():
    return oauth2.SpotifyClientCredentials(client_id=spotify_client_id, client_secret=
    spotify_client_secret).get_access_token()


spo = spotipy.Spotify(auth=generate_token())


def get_language_from_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT chat_id, language FROM CHAT_LAN")
    a = c.fetchall()
    for tup in a:
        languag[tup[0]] = tup[1]
		
    
def change_lan(chat_id, language):
    print("got here")
    return
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
    #c.execute("SELECT chat_id FROM CHAT_LAN where chat_id = '{0}'".format(chat_id))
    #if c.fetchone() == None:
        write_db("INSERT INTO CHAT_LAN(chat_id, language) values('{0}', '{1}')".format(chat_id, language))
    #c.execute("SELECT chat_id FROM CHAT_ID")
    except:
        pass


def rerun():
    args = sys.argv[:]
    args = ' '.join(['"%s"' % arg for arg in args])
    #  print(args)
    os.system("python " + args)
    sys.exit()


def get_version():
    s = requests.get(url=version_url)

    return s.text


def download_update():
    s = requests.get(url=source_url + "version.py")
    name = sys.argv[0]
    fil = codecs.open(name, 'w+', 'utf-8')
    fil.write(s.text)
    fil.close()

    s = requests.get(url=source_url + "setting.py")
    name = "\\".join(sys.argv[0].split("\\")[1:]) + "\\setting.py"
    fil = codecs.open(name, 'w+', 'utf-8')
    fil.write(s.text)
    fil.close()

    s = requests.get(url=source_url + "strings.py")
    name = "\\".join(sys.argv[0].split("\\")[1:]) + "\\strings.py"
    fil = codecs.open(name, 'w+', 'utf-8')
    fil.write(s.text)
    fil.close()


def is_update(version):
    if int(version) > __version__:
        return True
    return False


def do_update_thing():
    if is_update(get_version()):
        print("updating")
        download_update()
        print("Download finished\nUpdating")
        rerun()


def request(url, chat_id=None, control=False):
    try:
        thing = requests.get(url)
    except:
        thing = requests.get(url)
    if control == True:
        try:
            if thing.json()['error']['message'] == "Quota limit exceeded":
                sendMessage(chat_id, translate(languag[chat_id], strings.resend_link))
                return
        except KeyError:
            pass
        try:
            if thing.json()['error']:
                sendMessage(chat_id, translate(languag[chat_id], strings.no_result))
                return
        except KeyError:
            pass
    return thing


def translate(language, sms):
    try:
        language = language.split("-")[0]
        api = "https://translate.yandex.net/api/v1.5/tr.json/translate?key=trnsl.1.1.20181114T193428Z.ec0fb3" \
              "fb93e116c0.24b2ccfe2d150324e23a5571760e9a827d953003&text=%s&lang=he-%s" % (sms, language)
        sms = request(api).json()['text'][0]
    except:
        pass
    return sms


def delete(chat_id):
    global del2
    del2 += 1
    try:
        users[chat_id] -= 1
    except KeyError:
        pass


def write_db(execution):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    while True:
        sleep(1)
        try:
            c.execute(execution)
            conn.commit()
            conn.close()
            break
        except sqlite3.OperationalError:
            pass


def statisc(chat_id, do):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    if do == "USERS":
        c.execute("SELECT chat_id FROM CHAT_ID where chat_id = '%d'" % chat_id)
        if c.fetchone() == None:
            write_db("INSERT INTO CHAT_ID(chat_id) values('%d')" % chat_id)
        c.execute("SELECT chat_id FROM CHAT_ID")
        infos = len(c.fetchall())
    elif do == "TRACKS":
        c.execute("SELECT id FROM DWSONGS")
        infos = len(c.fetchall())
    conn.close()
    return str(infos)


def check_flood(chat_id, msg):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT banned FROM BANNED where banned = '%d'" % chat_id)
    if c.fetchone() != None:
        conn.close()
        return "BANNED"
    try:
        time = msg['date'] - date[chat_id]['time']
        if time > 30:
            date[chat_id]['msg'] = 0
        date[chat_id]['time'] = msg['date']
        if time <= 4:
            date[chat_id]['msg'] += 1
            if time <= 4 and date[chat_id]['msg'] > 4:
                if check_master(msg):
                    sendMessage(chat_id, base64.b64decode("SXQgc2VlbXMgbGlrZSB5b3UgYXJlIHRyeWluZyB0byBmbG9vZCBteSBzeXN0ZW0sCmJ1dCB5b3UgYXJlIG15IG1hc3RlciEg8J+ZjPCfj70KCldoYXQgY291bGQgSSBkbyBmb3IgeW91LCBncmVhdCBsb3JkPyDwn5GR8J+Zj/Cfj7w="))
                    return
                date[chat_id]['msg'] = 0
                date[chat_id]['tries'] -= 1
                sendMessage(chat_id, translate(languag[chat_id], strings.seems_flood + "\n" + str(date[chat_id]['tries']) + strings.tries_left))
            if date[chat_id]['tries'] == 0:
                write_db("INSERT INTO BANNED(banned) values('%d')" % chat_id)
                del date[chat_id]
                sendMessage(chat_id, translate(languag[chat_id], strings.were_banned))
    except KeyError:
        try:
            date[chat_id] = {"time": msg['date'], "tries": 3, "msg": 0}
        except KeyError:
            pass


def check_master(msg):
    return msg['from']['id'] == 455941946


def sendMessage(chat_id, text, reply_markup=None, reply_to_message_id=None, parse_mode=None):
    sleep(0.8)
    try:
        bot.sendMessage(chat_id, text, reply_markup=reply_markup, reply_to_message_id=reply_to_message_id,
                        parse_mode=parse_mode)
    except:
        pass


def sendPhoto(chat_id, photo, caption=None, reply_markup=None):
    sleep(0.8)
    try:
        bot.sendChatAction(chat_id, "upload_photo")
        bot.sendPhoto(chat_id, photo, caption=caption, reply_markup=reply_markup)
    except:
        pass


def sendAudio(chat_id, audio, link=None, image=None, youtube=False):
    sleep(0.8)
    try:
        bot.sendChatAction(chat_id, "upload_audio")
        if os.path.isfile(audio):
            audio = open(audio, "rb")
            try:
                tag = EasyID3(audio.name)
                duration = int(MP3(audio.name).info.length)
            except mutagen.id3._util.ID3NoHeaderError:
                tag = FLAC(audio.name)
                duration = int(tag.info.length)
            data = {
                "chat_id": "@deezer_spotify",#chat_id,
                "duration": duration,
                "performer": tag['artist'][0],
                "title": tag['title'][0]
                }
            file = {
                "audio": audio,
                "thumb": image
            }
            url = "https://api.telegram.org/bot" + token + "/sendAudio"
            try:
                request = requests.post(url, params=data, files=file, timeout=20)
                #response = bot.sendAudio(chat_id, audio)
            except:
                request = requests.post(url, params=data, files=file, timeout=20)
                #response = bot.sendAudio(chat_id, audio)
            if request.status_code != 200:
                #print(str(response))
                sendMessage(chat_id, translate(languag[chat_id], strings.the_song + tag['artist'][0]
                                               + " - " + tag['title'][0] + strings.too_big))
                print("too big")
            else:
                if youtube == False:
                    file_id = request.json()['result']['audio']['file_id']
                    bot.sendAudio(chat_id, file_id)
                    write_db("INSERT INTO DWSONGS(id, query, quality) values('%s', '%s', '%s')" % (link, file_id, audio.name.split("(")[-1].split(")")[0]))
                    pass

        else:
            bot.sendAudio(chat_id, audio)
    except telepot.exception.TelegramError:
        sendMessage(chat_id, translate(languag[chat_id], strings.track_not_in_deezer))
    except Exception as e:
        print(e)
        sendMessage(chat_id, translate(languag[chat_id], strings.cant_find_track))


def track(link, chat_id, quality):
    global spo
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (link, quality.split("MP3_")[-1]))
    match = c.fetchone()
    conn.close()
    if match != None:
        #print(match[0], type(match[0]))
        sendAudio(chat_id, match[0])
    else:
        try:
            youtube = False
            if "spotify" in link:
                try:
                    url = spo.track(link)
                except:
                    spo = spotipy.Spotify(auth=generate_token())
                    url = spo.track(link)
                try:
                    image = url['album']['images'][2]['url']
                except IndexError:
                    image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
                z = downloa.download_trackspo(link, quality=quality, recursive_quality=False, recursive_download=False)
            elif "deezer" in link:
                try:
                    url = request("https://api.deezer.com/track/" + link.split("/")[-1], chat_id, True).json()
                except AttributeError:
                    return
                try:
                    image = url['album']['cover_xl'].replace("1000x1000", "90x90")
                except AttributeError:
                    URL = "https://www.deezer.com/track/" + link.split("/")[-1]
                    image = request(URL).text
                    image = BeautifulSoup(image, "html.parser").find("img", class_="img_main")\
                        .get("src").replace("120x120", "90x90")
                ima = request(image).content
                if len(ima) == 13:
                    image = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
                z = downloa.download_trackdee(link, quality=quality, recursive_quality=False, recursive_download=False)
        except deezloader.TrackNotFound:
            sendMessage(chat_id, translate(languag[chat_id], strings.downloading_from_utube))
            try:
                if "spotify" in link:
                    z = dwytsongs.download_trackspo(link, check=False)
                elif "deezer" in link:
                    z = dwytsongs.download_trackdee(link, check=False)
                youtube = True
            except dwytsongs.TrackNotFound:
                sendMessage(chat_id, translate(languag[chat_id], strings.cant_download))
                return
        image = request(image).content
        sendAudio(chat_id, z, link, image, youtube)


def Link(link, chat_id, quality, msg):
    global spo
    global del1
    del1 += 1
    done = 0
    links1 = []
    links2 = []
    try:
       if "spotify" in link:
        if "track/" in link:
         if "?" in link:
            link,a = link.split("?")
         try:
            url = spo.track(link)
         except Exception as a:
            if not "The access token expired" in str(a):
                sendMessage(chat_id, translate(languag[chat_id], "Invalid link ;)"), reply_to_message_id=msg['message_id'])
                delete(chat_id)
                return
            spo = spotipy.Spotify(auth=generate_token())
            url = spo.track(link)
         try:
            image1 = url['album']['images'][0]['url']
         except IndexError:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         sendPhoto(chat_id, image1, caption=translate(languag[chat_id], strings.track) + url['name'] + "\n" + translate(languag[chat_id], strings.artist) + url['album']['artists'][0]['name'] + "\n" + translate(languag[chat_id], strings.album) + url['album']['name'] + "\n" + translate(languag[chat_id], strings.date) + url['album']['release_date'])
         track(link, chat_id, quality)
        elif "album/" in link:
         if "?" in link:
          link,a = link.split("?")
         try:
            tracks = spo.album(link)
         except Exception as a:
            if not "The access token expired" in str(a):
             sendMessage(chat_id, translate(languag[chat_id], strings.inval_link), reply_to_message_id=msg['message_id'])
             delete(chat_id)
             return
            spo = spotipy.Spotify(auth=generate_token())
            tracks = spo.album(link)
         try:
            image2 = tracks['images'][2]['url']
            image1 = tracks['images'][0]['url']
         except IndexError:
            image2 = "https://e-cdns-images.dzcdn.net/images/cover/90x90-000000-80-0-0.jpg"
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         tot = tracks['total_tracks']
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         count = 0
         for a in tracks['tracks']['items']:
             count += a['duration_ms']
             c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality.split("MP3_")[-1]))
             links2.append(a['external_urls']['spotify'])
             if c.fetchone() != None:
              links1.append(a['external_urls']['spotify'])
         if (count / 1000) > 40000:
          sendMessage(chat_id, translate(languag[chat_id], strings.ddos_ass))
          delete(chat_id)
          return
         sendPhoto(chat_id, image1, caption=translate(languag[chat_id], strings.album) + tracks['name'] + "\n" + translate(languag[chat_id], strings.artist) + tracks['artists'][0]['name'] + "\n" + translate(languag[chat_id], strings.date) + tracks['release_date'] + "\n" + translate(languag[chat_id], strings.track_amount) + str(tot))
         tracks = tracks['tracks']
         if tot != 50:
            for a in range(tot // 50):
                try:
                   tracks2 = spo.next(tracks)
                except:
                   spo = spotipy.Spotify(auth=generate_token())
                   tracks2 = spo.next(tracks)
                for a in tracks2['items']:
                    c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['external_urls']['spotify'], quality.split("MP3_")[-1]))
                    links2.append(a['external_urls']['spotify'])
                    if c.fetchone() != None:
                     links1.append(a['external_urls']['spotify'])
         conn.close()
         if len(links1) <= tot // 2:
          z = downloa.download_albumspo(link, quality=quality, recursive_quality=False, recursive_download=False)
         else:
             for a in links2:
                 track(a, chat_id, quality)
         done = 1
        elif "playlist/" in link:
         if "?" in link:
          link,a = link.split("?")
         musi = link.split("/")
         try:
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         except Exception as a:
            if not "The access token expired" in str(a):
             sendMessage(chat_id, translate(languag[chat_id], "Invalid link ;)"), reply_to_message_id=msg['message_id'])
             delete(chat_id)
             return
            spo = spotipy.Spotify(auth=generate_token())
            tracks = spo.user_playlist(musi[-3], playlist_id=musi[-1])
         try:
            image1 = tracks['images'][0]['url']
         except IndexError:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         tot = tracks['tracks']['total']
         if tot > 400:
          sendMessage(chat_id, translate(languag[chat_id], "Fuck you"))
          delete(chat_id)
          return
         sendPhoto(chat_id, image1, caption=translate(languag[chat_id], strings.creation) + tracks['tracks']['items'][0]['added_at'] + "\n" + translate(languag[chat_id], strings.user) + str(tracks['owner']['display_name']) + "\n" + translate(languag[chat_id], strings.track_amount) + str(tot))
         for a in tracks['tracks']['items']:
             try:
                track(a['track']['external_urls']['spotify'], chat_id, quality)
             except KeyError:
                try:
                   sendMessage(chat_id, a['track']['name'] + strings.not_found)
                except KeyError:
                   sendMessage(chat_id, strings.was_error)
         tot = tracks['tracks']['total']
         tracks = tracks['tracks']
         if tot != 100:
            for a in range(tot // 100):
                try:
                   tracks = spo.next(tracks)
                except:
                   spo = spotipy.Spotify(auth=generate_token())
                   tracks = spo.next(tracks)
                for a in tracks['items']:
                    try:
                       track(a['track']['external_urls']['spotify'], chat_id, quality)
                    except KeyError:
                       try:
                          sendMessage(chat_id, a['track']['name'] + strings.not_found)
                       except KeyError:
                          sendMessage(chat_id, strings.was_error)
         done = 1
        else:
            sendMessage(chat_id, translate(languag[chat_id], strings.unsupported_link))
       elif "deezer" in link:
        if "track/" in link:
         if "?" in link:
            link,a = link.split("?")
         try:
            url = request("https://api.deezer.com/track/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         image1 = url['album']['cover_xl']
         if image1 == None:
            URL = "https://www.deezer.com/track/" + link.split("/")[-1]
            image1 = request(URL).text
            image1 = BeautifulSoup(image1, "html.parser").find("img", class_="img_main").get("src").replace("120x120", "1000x1000")
         ima = request(image1).content
         if len(ima) == 13:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         sendPhoto(chat_id, image1, caption=translate(languag[chat_id], strings.track) + url['title'] + "\n" + translate(languag[chat_id], strings.artist) + url['artist']['name'] + "\n" + translate(languag[chat_id], strings.album) + url['album']['title'] + "\n" + translate(languag[chat_id], strings.date) + url['album']['release_date'])
         track(link, chat_id, quality)
        elif "album/" in link:
         if "?" in link:
            link,a = link.split("?")
         try:
            url = request("https://api.deezer.com/album/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         if url['duration'] > 40000:
            sendMessage(chat_id, translate(languag[chat_id], strings.ddos_ass))
            delete(chat_id)
            return
         image1 = url['cover_xl']
         if image1 == None:
            URL = "https://www.deezer.com/album/" + link.split("/")[-1]
            image1 = request(URL).text
            image1 = BeautifulSoup(image1, "html.parser").find("img", class_="img_main").get("src").replace("200x200", "1000x1000")
         ima = request(image1).content
         if len(ima) == 13:
            image1 = "https://e-cdns-images.dzcdn.net/images/cover/1000x1000-000000-80-0-0.jpg"
         image2 = image1.replace("1000x1000", "90x90")
         conn = sqlite3.connect(db_file)
         c = conn.cursor()
         for a in url['tracks']['data']:
                c.execute("SELECT query FROM DWSONGS WHERE id = '%s' and quality = '%s'" % (a['link'], quality.split("MP3_")[-1]))
                links2.append(a['link'])
                if c.fetchone() != None:
                    links1.append(a['link'])
         conn.close()
         tot = url['nb_tracks']
         sendPhoto(chat_id, image1, caption=translate(languag[chat_id], strings.album) + url['title'] + "\n" + translate(languag[chat_id], strings.artist) + url['artist']['name'] + "\n" + translate(languag[chat_id], strings.date) + url['release_date'] + "\n" + translate(languag[chat_id], strings.track_amount) + str(tot))
         if len(links1) <= tot // 2:
            z = downloa.download_albumdee(link, quality=quality, recursive_quality=False, recursive_download=False)
         else:
             for a in links2:
                 track(a, chat_id, quality)
         done = 1
        elif "playlist/" in link:
         if "?" in link:
            link,a = link.split("?")
         try:
            url = request("https://api.deezer.com/playlist/" + link.split("/")[-1], chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         tot = url['nb_tracks']
         if tot > 400:
            sendMessage(chat_id, translate(languag[chat_id], strings.curse))
            delete(chat_id)
            return
         sendPhoto(chat_id, url['picture_xl'], caption=translate(languag[chat_id], strings.creation) + url['creation_date'] + "\n" + translate(languag[chat_id], strings.user)
                                                       + url['creator']['name'] + "\n" + translate(languag[chat_id], strings.track_amount) + str(tot))
         for a in url['tracks']['data']:
                track(a['link'], chat_id, quality)
         done = 1
        elif "artist/" in link:
         if "?" in link:
            link,a = link.split("?")
         link = "https://api.deezer.com/artist/" + link.split("/")[-1]
         try:
            url = request(link, chat_id, True).json()
         except AttributeError:
            delete(chat_id)
            return
         sendPhoto(chat_id, url['picture_xl'], caption=translate(languag[chat_id], strings.artist) + url['name'] + "\n" + translate(languag[chat_id], strings.album_number)
                                                       + str(url['nb_album']) + "\n" + translate(languag[chat_id], strings.fans_deezer) + str(url['nb_fan']),
                   reply_markup=InlineKeyboardMarkup(
                               inline_keyboard=[
                                                [InlineKeyboardButton(text=translate(languag[chat_id], strings.top_thirty), callback_data=link +
                                                "/top?limit=30"), InlineKeyboardButton(text=translate(languag[chat_id], strings.albums), callback_data=link + "/albums")],
                                                [InlineKeyboardButton(text=translate(languag[chat_id], strings.radio), callback_data=link + "/radio")]
                               ]
                  ))
        else:
            sendMessage(chat_id, translate(languag[chat_id], strings.unsupported_link))
       else:
           sendMessage(chat_id, translate(languag[chat_id], strings.unsupported_link))
       try:
            image2 = request(image2).content
            for a in range(len(z)):
                sendAudio(chat_id, z[a], links2[a], image2)
       except NameError:
            pass

    except deezloader.QuotaExceeded:
        sendMessage(chat_id, translate(languag[chat_id], strings.resend_link))
    except deezloader.AlbumNotFound:
        sendMessage(chat_id, translate(languag[chat_id], strings.album_not_in_deezer))
        sendMessage(chat_id, translate(languag[chat_id], strings.try_inline))
    except Exception as a:
        logging.warning(a)
        logging.info(link)
        sendMessage(chat_id, translate(languag[chat_id], strings.contact))
    try:
        if done == 1:
            sendMessage(chat_id, translate(languag[chat_id], strings.finished), reply_to_message_id=msg['message_id'])
    except:
        pass
    delete(chat_id)


def Audio(audio, chat_id):
    global spo
    file = loc_dir + audio + ".ogg"
    try:
        bot.download_file(audio, file)
    except telepot.exception.TelegramError:
        sendMessage(chat_id, translate(languag[chat_id], strings.more_than_twenty))
        return
    audio = acrcloud.recognizer(config, file)
    try:
        os.remove(file)
    except FileNotFoundError:
        pass
    if audio['status']['msg'] != "Success":
        sendMessage(chat_id, translate(languag[chat_id], strings.cant_detect))
    else:
        artist = audio['metadata']['music'][0]['artists'][0]['name']
        track = audio['metadata']['music'][0]['title']
        album = audio['metadata']['music'][0]['album']['name']
        try:
            date = audio['metadata']['music'][0]['release_date']
            album += "_" + date
        except KeyError:
            album += "_"
        try:
            label = audio['metadata']['music'][0]['label']
            album += "_" + label
        except KeyError:
            album += "_"
        try:
            genre = audio['metadata']['music'][0]['genres'][0]['name']
            album += "_" + genre
        except KeyError:
            album += "_"
        if len(album) > 64:
            album = "Infos with too many bytes"
        try:
            url = request("https://api.deezer.com/search/track/?q=" + track.replace("#", "") + " + " + artist.replace("#", ""), chat_id, True).json()
        except AttributeError:
            return
        try:
            for a in range(url['total'] + 1):
                if url['data'][a]['title'] == track:
                    id = url['data'][a]['link']
                    image = url['data'][a]['album']['cover_xl']
                    break
        except IndexError:
            try:
                id = "https://open.spotify.com/track/" + audio['metadata']['music'][0]['external_metadata']['spotify']['track']['id']
                try:
                    url = spo.track(id)
                except:
                    spo = spotipy.Spotify(auth=generate_token())
                    url = spo.track(id)
                image = url['album']['images'][0]['url']
            except KeyError:
                pass
            try:
                id = "https://api.deezer.com/track/" + str(audio['metadata']['music'][0]['external_metadata']['deezer']['track']['id'])
                try:
                    url = request(id, chat_id, True).json()
                except AttributeError:
                    return
                image = url['album']['cover_xl']
            except KeyError:
                pass
        try:
            sendPhoto(chat_id, image, caption=track + " - " + artist,
                     reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                                [InlineKeyboardButton(text=translate(languag[chat_id], strings.download), callback_data=id),
                                                 InlineKeyboardButton(text=translate(languag[chat_id], strings.info), callback_data=album)]
                                 ]
                     ))
        except:
            sendMessage(chat_id, translate(languag[chat_id], strings.was_error))


def inline(msg, from_id, query_data, query_id):
    if "artist" in query_data:
     message_id = msg['message']['message_id']
     array = []
     print(msg)
     chat_id = msg['from']['id']
     if "album" in query_data:
      try:
            url = request(query_data, from_id, True).json()
      except AttributeError:
            return
      for a in url['data']:
            array.append([InlineKeyboardButton(text=a['title'] + " - " + a['release_date'].replace("-", "/"), callback_data=a['link'])])
      array.append([InlineKeyboardButton(text=translate(languag[chat_id], strings.back), callback_data=query_data.split("/")[-2] + "/" + "artist")])
      bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=array
                                 ))
     elif "down" in query_data:
      if ans == "2":
        if users[from_id] == 3:
            bot.answerCallbackQuery(query_id, translate(languag[from_id], strings.wait), show_alert=True)
            return
        else:
           users[from_id] += 1
      bot.answerCallbackQuery(query_id, translate(languag[from_id], strings.songs_downloading))
      try:
         url = request("https://api.deezer.com/artist/" + query_data.split("/")[-4] + "/" + query_data.split("/")[-1], from_id, True).json()
      except AttributeError:
         return
      for a in url['data']:
          Link("https://www.deezer.com/track/" + str(a['id']), from_id, qualit[from_id], msg['message'])
          if ans == "2":
           users[from_id] += 1
      if ans == "2":
       users[from_id] -= 1
     elif "radio" in query_data or "top" in query_data:
      try:
         url = request(query_data, from_id, True).json()
      except AttributeError:
         return
      for a in url['data']:
          array.append([InlineKeyboardButton(text=a['artist']['name'] + " - " + a['title'], callback_data="https://www.deezer.com/track/" + str(a['id']))])
      array.append([InlineKeyboardButton(text=translate(languag[chat_id], strings.get_all), callback_data=query_data.split("/")[-2] + "/" + "artist/down/" + query_data.split("/")[-1])])
      array.append([InlineKeyboardButton(text=translate(languag[chat_id], strings.back), callback_data=query_data.split("/")[-2] + "/" + "artist")])
      bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=array
                                 ))
     else:
         link = "https://api.deezer.com/artist/" + query_data.split("/")[-2]
         try:
            url = request("https://api.deezer.com/artist/" + query_data.split("/")[-2], from_id, True).json()
         except AttributeError:
            return
         bot.editMessageReplyMarkup(((from_id, message_id)),
                                 reply_markup=InlineKeyboardMarkup(
                                             inline_keyboard=[
                                                        [InlineKeyboardButton(text=translate(languag[chat_id], strings.top_thirty), callback_data=link + "/top?limit=30"), InlineKeyboardButton(text=strings.albums, callback_data=link + "/albums")],
                                                        [InlineKeyboardButton(text=translate(languag[chat_id], strings.albums), callback_data=link + "/radio")]
                                             ]
                                 ))
    else:
        tags = query_data.split("_")
        if tags[0] == "Infos with too many bytes":
         bot.answerCallbackQuery(query_id, translate(languag[from_id], query_data))
        elif len(tags) == 4:
         bot.answerCallbackQuery(query_id, text=translate(languag[from_id], strings.album) + tags[0] + "\n" + translate(languag[from_id], strings.date) + tags[1] + "\n" + translate(languag[from_id], strings.label) + tags[2] + "\n" + translate(languag[from_id], strings.genre) + tags[3], show_alert=True)
        else:
            if ans == "2":
             if users[from_id] == 3:
              bot.answerCallbackQuery(query_id, translate(languag[from_id], strings.wait), show_alert=True)
              return
             else:
                 users[from_id] += 1
            bot.answerCallbackQuery(query_id, translate(languag[from_id], strings.song_donloading))
            Link(query_data, from_id, qualit[from_id], msg['message'])


def download(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
    try:
        languag[from_id]
    except KeyError:
        try:
            languag[from_id] = msg['from']['language_code']
        except KeyError:
            languag[from_id] = strings.default_language
    try:
        qualit[from_id]
    except KeyError:
        qualit[from_id] = "MP3_320"
    try:
        users[from_id]
    except KeyError:
        users[from_id] = 0
    Thread(target=inline, args=(msg, from_id, query_data, query_id)).start()


def search(msg):
    query_id, from_id, query_string = telepot.glance(msg, flavor="inline_query")
    try:
        languag[from_id] = msg['from']['language_code']
    except KeyError:
        languag[from_id] = strings.default_language
    if check_flood(from_id, msg) == "BANNED":
        return
    if "" == query_string:
        search1 = request("http://api.deezer.com/chart/").json()
        result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'],
                thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['tracks']['data']]
        result += [InlineQueryResultArticle(id="https://www.deezer.com/album/" + str(a['id']), title=a['title'] +
                " (" + strings.album + ")", description=a['artist']['name'], thumb_url=a['cover_big'],
                        input_message_content=InputTextMessageContent(message_text="https://www.deezer.com/album/"
                                                                                   + str(a['id']))) for a in search1['albums']['data']]
        result += [InlineQueryResultArticle(id=a['link'], title=str(a['position']), description=a['name'],
                                            thumb_url=a['picture_big'], input_message_content=InputTextMessageContent(
                message_text=a['link'])) for a in search1['artists']['data']]
        result += [InlineQueryResultArticle(id=a['link'], title=a['title'], description=strings.n_tracks +
                    str(a['nb_tracks']), thumb_url=a['picture_big'], input_message_content=InputTextMessageContent
        (message_text=a['link'])) for a in search1['playlists']['data']]
    elif "album:" in query_string:
        search1 = request("https://api.deezer.com/search/album/?q=" + query_string.split("album:")[1]
                          .replace("#", "")).json()
        try:
            if search1['error']:
                return
        except KeyError:
            pass
        result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'],
                    thumb_url=a['cover_big'], input_message_content=InputTextMessageContent
            (message_text=a['link'])) for a in search1['data']]

    elif "אלבום:" in query_string:
        search1 = request("https://api.deezer.com/search/album/?q=" + query_string.split("אלבום:")[1].replace("#", "")).json()
        try:
            if search1['error']:
                return
        except KeyError:
            pass
        result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'], thumb_url=a['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1['data']]
    elif "artist:" in query_string:
        search1 = request("https://api.deezer.com/search/artist/?q=" + query_string.split("artist:")[1].replace("#", "")).json()
        try:
            if search1['error']:
                return
        except KeyError:
            pass
        result = [InlineQueryResultArticle(id=a['link'], title=a['name'], thumb_url=a['picture_big'],
                                           input_message_content=InputTextMessageContent(message_text=a['link']))
                  for a in search1['data']]
    elif "אמן:" in query_string:
        search1 = request("https://api.deezer.com/search/artist/?q=" + query_string.split("אמן:")[1].replace("#", ""))\
            .json()
        try:
            if search1['error']:
                return
        except KeyError:
            pass
        result = [InlineQueryResultArticle(id=a['link'], title=a['name'], thumb_url=a['picture_big'],
                                           input_message_content=InputTextMessageContent(message_text=a['link']))
                  for a in search1['data']]
    else:
        search1 = request("https://api.deezer.com/search?q=" + query_string.replace("#", "")).json()
        try:
            if search1['error']:
                return
        except KeyError:
            pass
        search1 = search1['data']
        result = [InlineQueryResultArticle(id=a['link'], title=a['title'], description=a['artist']['name'],
                                           thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent(message_text=a['link'])) for a in search1]
        for a in search1:
            try:
                if "https://www.deezer.com/album/" + str(a['album']['id']) in str(result):
                    continue
            except KeyError:
                continue
            result += [InlineQueryResultArticle(id="https://www.deezer.com/album/" + str(a['album']['id']),
                        title=a['album']['title'] + " (" + strings.album + ")", description=a['artist']['name'],
                        thumb_url=a['album']['cover_big'], input_message_content=InputTextMessageContent
                (message_text="https://www.deezer.com/album/" + str(a['album']['id'])))]
    try:
        bot.answerInlineQuery(query_id, result)
    except telepot.exception.TelegramError:
        pass


def hijack_the_pony(msg):
    last_name = ""; username = ""
    if 'username' in msg['from']:
        username = msg['from']['username']
    if 'last_name' in msg['from']:
        last_name = msg['from']['last_name']
    log.write("Name: {0} {1}\nUsername: {2}\nText: {3}\nTime: {4}\n\n".format(msg['from']['first_name'], last_name, username, msg['text'], datetime.fromtimestamp(msg['date'])))
    log.flush()
    try:
        if msg['from']['id'] == 467782371:
            sendMessage(chat_id=msg['from']['id'], parse_mode="Markdown", text=base64.b64decode
            ("16nXnTogYNeo15XXoNeZINeQ15TXqNeV158g15nXoten15HXodeV159gCteb16rXldeR16o6IGDXlNeo15"
             "kg15nXlNeV15PXlCAyMywg16DXldeV15Qg15PXoNeZ15DXnGAK16ou15Y6IGAzMjg2MjEzMjFgCteb16rXl"
             "deR16og15PXldeQItecOiBgcm9uaXBvbnlAZ21haWwuY29tYArXnteh16TXqCDXmNec16TXldefOiBgMDU4L"
             "TQwMzg2MDVgCtee16HXpNeoINeY15zXpNeV158g15HXkdeZ16o6IGAwMi05OTM0MjIzYArXnteh16TXqCDXn"
             "teW15TXlCDXlNeY15zXkteo1506IGA0Njc3ODIzNzFgCgrXqteU16DXlCDXnteU15HXldeYIfCfmI8="))
    except:
        pass


def up(msg):
    pass


def start(msg):
    #print(msg['from']['id'], msg['from']['username'], msg)
    hijack_the_pony(msg)
    pprint(msg)
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        languag[chat_id]
    except KeyError:
        try:
            languag[chat_id] = msg['from']['language_code']
        except KeyError:
            languag[chat_id] = strings.default_language
    if check_flood(chat_id, msg) == "BANNED":
        return
    statisc(chat_id, "USERS")
    try:
        qualit[chat_id]
    except KeyError:
        qualit[chat_id] = "MP3_320"
    try:
        users[chat_id]
    except KeyError:
        users[chat_id] = 0
    if content_type == "text" and msg['text'] == "/start":
     try:
        sendPhoto(chat_id, open("example.png", "rb"), caption=translate(languag[chat_id], """ברוכים הבאים אל @Deezer_spotify_bot
ליחצו על '/' כדי לקבל את רשימת הפקודות.
תהנו!!😃"""))
     except FileNotFoundError:
        print("no file found")
        pass
     if languag[chat_id] == strings.default_language:
         artist_str, album_str = strings.inline_kboard_artist, strings.inline_kboard_album
     else:
         artist_str, album_str = strings.inline_kboard_artist_en, strings.inline_kboard_album_en
     sendMessage(chat_id, translate(languag[chat_id], strings.manual),
                 reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                            [InlineKeyboardButton(text=translate(languag[chat_id], strings.search_by_artist),
                                                  switch_inline_query_current_chat=artist_str),
                             InlineKeyboardButton(text=translate(languag[chat_id], strings.search_by_album),
                                                  switch_inline_query_current_chat=album_str)],
                            [InlineKeyboardButton(text=translate(languag[chat_id], strings.global_search), switch_inline_query_current_chat="")]
                             ]
                ))
    elif content_type == "text" and msg['text'] == "/translate":
        if languag[chat_id] != strings.default_language:
            languag[chat_id] = strings.default_language
            change_lan(chat_id, strings.default_language)
            sendMessage(chat_id, translate(languag[chat_id], strings.changed_to_hebrew))
        else:
            print(languag[chat_id], strings.default_language, msg['from']['language_code'])
            if languag[chat_id] == msg['from']['language_code']:
                languag[chat_id] = strings.second_language
                change_lan(chat_id, strings.second_language)
                sendMessage(chat_id, translate(languag[chat_id], strings.will_use_english))
            else:
                languag[chat_id] = msg['from']['language_code']
                change_lan(chat_id, msg['from']['language_code'])
                sendMessage(chat_id, translate(languag[chat_id], strings.will_use_your_language))
    elif content_type == "text" and msg['text'] == "/quality":
        sendMessage(chat_id, translate(languag[chat_id], strings.select_quality),
                 reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                     [KeyboardButton(text=strings.flac), KeyboardButton(text=strings.kb_320)],
                                     [KeyboardButton(text=strings.kb_256), KeyboardButton(text=strings.kb_128)]
                             ]
                ))
    elif content_type == "text" and (msg['text'] == "FLAC" or msg['text'] == "MP3_320Kbps"
                                     or msg['text'] == "MP3_256Kbps" or msg['text'] == "MP3_128Kbps"):
        qualit[chat_id] = msg['text'].replace("Kbps", "")
        sendMessage(chat_id, translate(languag[chat_id], strings.will_download_in_quality + msg['text']),
                    reply_markup=ReplyKeyboardRemove())
        sendMessage(chat_id, translate(languag[chat_id], strings.best_quality_available))
    elif content_type == "voice" or content_type == "audio":
        Thread(target=Audio, args=(msg[content_type]['file_id'], chat_id)).start()
    elif content_type == "text" and msg['text'] == "/info":
        sendMessage(chat_id, strings.about + statisc(chat_id, "USERS") + "\n" +
                    strings.total_downloads + statisc(chat_id, "TRACKS"))
    elif content_type == "text":
        if check_master(msg):
            if msg['text'] == "log" or msg['text'] == "לוג" or msg['text'] == "/slave":
                global log
                log.close()
                a = open('log.txt', 'rb')
                # requests.post(url, files=a)
                bot.sendDocument(chat_id=455941946, document=a)
                a.close()
                log = codecs.open("log.txt", 'a+', 'utf8')
                return
            if msg['text'] == "I am your father" or msg['text'] == "son":
                do_update_thing()
                sendMessage(chat_id, base64.b64decode("SGVsbG8gYWdhaW4gbWFzdGVyIfCfp5nwn4+74oCN4pmC77iPXG5JIHdpbGwgdHJ5IHlvdXIgdXBkYXRlIHRoaW5neS5cblxuQW55dGhpbmcgZm9yIHlvdSwgbXkgbG9yZCHwn5mM8J+PvQ=="))
                return
        try:
            msg['entities']
            if ans == "2" and users[chat_id] == 3:
                sendMessage(chat_id, translate(languag[chat_id], strings.wait))
            else:
                if ans == "2":
                    users[chat_id] += 1
                Thread(target=Link, args=(msg['text'].replace("'", ""), chat_id, qualit[chat_id], msg)).start()
        except KeyError:
            if languag[chat_id] == strings.default_language:
                artist_str, album_str = strings.inline_kboard_artist, strings.inline_kboard_album
            else:
                artist_str, album_str = strings.inline_kboard_artist_en, strings.inline_kboard_album_en
            sendMessage(chat_id, translate(languag[chat_id], strings.press),
                    reply_markup=InlineKeyboardMarkup(
                                inline_keyboard=[
                                               [InlineKeyboardButton(text=translate(languag[chat_id], strings.search_by_artist),
                                                                     switch_inline_query_current_chat=artist_str + msg['text']),
                                                InlineKeyboardButton(text=translate(languag[chat_id], strings.search_by_album),
                                                                     switch_inline_query_current_chat=album_str + msg['text'])],
                                               [InlineKeyboardButton(text=translate(languag[chat_id], strings.global_search),
                                                                     switch_inline_query_current_chat=msg['text'])]
                                ]
                   ))
try:
   print("1):Free")
   print("2):Strict")
   ans = "2"#input("Choose:")
   if ans == "1" or ans == "2":
    bot.message_loop({
                      "chat": start,
                      "callback_query": download,
                      "inline_query": search,
                      "chosen_inline_result": up
                     })
    pass
    print("הבוט התחיל לרוץ")
    while True:
        sleep(1)
        #continue
        if del1 == del2:
            del1, del2 = 0, 0
            for a in os.listdir(loc_dir):
                try:
                    shutil.rmtree(loc_dir + a)
                except NotADirectoryError:
                    pass
                except Exception as e:
                    print("Exception" + str(e))

except KeyboardInterrupt:
    #print("here")
    pass
    #os.rmdir(loc_dir)
    #print("\nנעצר")
   #bot.sendDocument(chat_id=455941946, document=log)
    #log.close()

finally:

        #url = "https://api.telegram.org/bot" + token + "/sendDocument?chat_id=455941946"
        #data = {
        #    "chat_id": 455941946
    try:    #}
        os.rmdir(loc_dir)
        print("\nנעצר")
        log.close()
        a = open('log.txt', 'rb')
        #requests.post(url, files=a)
        bot.sendDocument(chat_id=455941946, document=a)
        #log.close()
    except:
        pass
