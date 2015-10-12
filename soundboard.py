#! /usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "space"

"""
sounboard.py - Search through File Metadata
"""

import os, io, sys
import json
import hashlib

import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

VALID_TAGS = ['title', 'album', 'artist', 'albumartist', 'genre', 'creator', 'description', 'comment']

def _index_path(path):
	return "/tmp/" + hashlib.sha256(path.encode()).hexdigest() + ".json"

def get_index_from_file(path):
	index_path = _index_path(path)
	with io.open(index_path, 'r', encoding='utf8') as json_fh:
		return json.loads(json_fh.read())


def rebuild_index_file(path):
	index_path = _index_path(path)
	index = build_index_object(path)
	with io.open(index_path, 'w', encoding='utf8') as json_fh:
		json.dump(index, json_fh, ensure_ascii=False)


def build_index_object(path):
	from mutagen.id3._util import ID3NoHeaderError
	from mutagen.easyid3 import EasyID3
	from mutagen.oggvorbis import OggVorbis

	files = next(os.walk(path))[2]
	index = dict()

	for file in files:
		index[file] = list()
		index[file].append(file)
		meta = None

		try:
			if file.endswith(".mp3"):
				meta = EasyID3(path + file)
			elif file.endswith(".ogg"):
				meta = OggVorbis(path + file)
			else:
				log.info(str.format("No Parser for '%s'."% file ))
				continue
		except ID3NoHeaderError:
			log.warning(str.format("Failed to parse '%s': No ID3Header"% file))
			continue

		for thing in [meta[topic] for topic in meta if topic in VALID_TAGS]:
			index[file].append(*thing)

	return index


def search(to_find, index):
	from fuzzywuzzy import fuzz

	search_res = list()
	for key in index:
		max_score = max([fuzz.partial_ratio(to_find, thing) for thing in index[key]])
		search_res.append( (key, max_score) )
	
	search_res = sorted(search_res, key=lambda x: x[1])
	search_res = [thing[0] for thing in search_res]
	return search_res

def single_search(to_find, index):
	search_res = search(to_find, index)
	return (search_res[-1], len(search_res))


def main():
	import argparse

	parser = argparse.ArgumentParser(description="Soundboard CLI usage.")
	parser.add_argument('--rebuild-index-file',	dest='rebuild_index',	action='store_true',	help='Update index file.')
	parser.add_argument('--use-index-file',		dest='use_index',		action='store_true',	help='Use index filesd')
	parser.add_argument('--path',				dest='path',			help='Directory of soundboard files.', required=True)
	parser.add_argument('--search',				dest='to_find',			help='String to look for in file metadata.',)

	parser.set_defaults(rebuild_index=False, use_index=False)
	args = parser.parse_args()

	if args.rebuild_index:
		rebuild_index_file(args.path)

	if args.to_find:
		index = None

		if args.use_index:
			index = get_index_from_file(args.path)
		else:
			index = build_index_object(args.path)
		
		print(args.path + single_search(args.to_find, index)[0])


if __name__ == '__main__':
	main()
