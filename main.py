#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyrogram import Client, Filters
import sys
import os
import re
import requests
import codecs


__author__ = 'ידידיה לאופר'
__version__ = 11


version_url = "https://raw.githubusercontent.com/YedidyaLaufer/self_update/master/version"
source_url = "https://raw.githubusercontent.com/YedidyaLaufer/self_update/master/client.py"
upload_url = 'https://upload.cdncv.net/upload/01'
download_url = "https://cloudvideo.tv/"

app = Client("Yedidya Laufer")
video_types = ['avi', 'mkv', 'mpg', 'mpeg', 'vob', 'wmv', 'flv', 'mp4', 'mov', 'm4v', 'm2v', 'divx', 'xvid', '3gp',
				'webm', 'ogv', 'ogg', 'ts']


def rerun():
	os.spawnl(os.P_WAIT, sys.executable, *([sys.executable] +
										(sys.argv if __package__ is None else ["-m", __loader__.name] + sys.argv[
																										1:])))
	sys.exit()
	# args = sys.argv[:]
	# self.log('Re-spawning %s' % ' '.join(args))

	# args.insert(0, sys.executable)
	# if sys.platform == 'win32':
	# args = ['"%s"' % arg for arg in args]

	# os.chdir(_startup_cwd)
	# os.execv(sys.executable, args)


@app.on_message(Filters.document)
def my_handler(client, message):
	do_update_thing()

	if message.document:
		print("got document")
		if is_movie(message.document.file_name):
			print("is movie", message.document.file_name)
			# print(dir(message.document))
			message.reply("""קיבלתי👍
	מתחיל להוריד...📥""")
			down_path = client.download_media(message=message, progress=progress)
			if down_path is None:
				print("error in download")
				breakpoint()
			print("downloaded")
			message.reply("""ההורדה הסתיימה👌
	מעלה לצפיה ישירה⬆️""")
			name = down_path.split('\\')[-1]
			link = upload_file(down_path, name)
			message.reply("""הנה קישור לסרט שלך
	בצפיה ישירה ⛓""" + '\n' + link)
			# print(down_path)
		else:
			message.reply("""מצטער,😕
	זה לא קובץ של סרט🤷🏼‍♂️""")


def is_movie(st):
	end = st.split('.')[-1]
	if end in video_types:
		return True
	return False


def upload_file(file_path, file_name):
	fil = open(file_path, 'rb')
	multipart_form_data = {'file': (file_name, fil)}

	response = requests.post(url=upload_url, files=multipart_form_data)

	a = re.search('textarea name="fn"\>.+?\<', response.text)
	return download_url + a.group().split('textarea name="fn">')[-1][:-1]


def progress(client, current, total):
	print('{} out of {}'.format(current, total))


def get_version():

	s = requests.get(url=version_url)

	return s.text


def download_update():
	s = requests.get(url=source_url)
	name = sys.argv[0]
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


if __name__ == '__main__':
	print(__version__)
	do_update_thing()
