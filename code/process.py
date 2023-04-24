"""
Internet Archive upload program for digitized texts
Copyright (C) 2019  Jakob Cornell
Modified 2021-2022  Kurtis Vetter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For the full license text, see <https://www.gnu.org/licenses/>.
"""

import uuid
import csv
from pathlib import *
import tempfile, zipfile
import sys
import math
import time

import internetarchive as ia
import pandas

base_dir = Path('~/googledrive').expanduser()
# Constants, these are likely to change on each run
SHEET_NAME = 'DIMENOVELS-COMPLETE'
EXCEL_FILENAME = 'DimeNovelTestBatch.xls'
CONFIG_FILENAME = 'config.ini'
# this is a column in the spreadsheet
ID_COL = 'image_folder' # used to be 'scan_id'

def make_zip(scan_parent: PosixPath, ia_id):
	"""
	Create a temporary zip file for an upload, add page scans, and return it
	NOTE: If you receive OSError (error 28), you need to add more space to
	your tmpfs filesystem mounted at /tmp. To do so, edit /etc/fstab and add
	size="<more space>" to the tmpfs line
	"""
	tf = tempfile.TemporaryFile(mode = 'w+b')
	with zipfile.ZipFile(tf, mode = 'w') as zf:
		to_compress = 0
		for i in scan_parent.iterdir():
			to_compress += 1
		i = 1
		for img in scan_parent.iterdir():
			print("Adding file {}/{} to {} archive    ".format(i, to_compress, scan_parent.name), end='\r')
			if not img.name.lower().endswith('.xml'):
				# arc_name = '{}/{}{}'.format(ia_id, ia_id, img.name[-9:])
				# zf.write(str(img), arcname = arc_name)
				zf.write(str(img))
			i += 1
		print("")
	tf.seek(0)
	return tf

def new_item(ia_sess):
	"""Get a new IA item to upload to."""
	new = lambda: ia_sess.get_item(str(uuid.uuid4()))
	item = new()
	while True:
		item = new()
		if not item.exists:
			return item
		time.sleep(0.5)

def fix_metadata(metadata):
	"""
	NOTE: metadata identifiers cannot have spaces
	see https://archive.org/services/docs/api/metadata-schema/index.html
	for more info
	"""
	new = {}
	for (k, v) in metadata.items():
		k = k.strip()
		k = k.replace(" ", "_")
		if k == 'docID': # 'docID' spreadsheet field gets uploaded as 'scan_id'
			k = ID_COL
		if v and not (isinstance(v, float) and math.isnan(v)): # Pandas seems to coerce empty cells to NaN
			new[k] = str(v)
	return new

def process_row(ia_sess, metadata, parent_path):
	"""
	Create and upload a zip for the given metadata, returning the IA ID uploaded to.
	metadata: dict -- item metadata: "fixed" metadata from Excel row
	parent_path: pathlib.Path -- path to parent directory of scan data directory
	"""
	scan_id = metadata[ID_COL]
	item = new_item(ia_sess)

	print("Creating a zip file for " + scan_id)
	with make_zip(parent_path.joinpath(scan_id), item.identifier) as zf:
		remote_name = scan_id + '_images.zip'
		ia.upload(
			identifier = item.identifier,
			files = {remote_name: zf},
			metadata = metadata,
			verbose = True
		)
	return item.identifier

def iter_excel(excel_path, sheet_to_path):
	"""
	Generate path (to scan directory) and metadata dict pairs for a given Excel file.
	sheet_to_path: function -- maps the name of an Excel sheet to the corresponding path (rel. to `base_dir`)
	"""
	with pandas.ExcelFile(excel_path) as excel:
		for sheet_name in excel.sheet_names:
			frame = excel.parse(sheet_name)
			for (_, series) in frame.iterrows():
				path = base_dir.joinpath(sheet_to_path(sheet_name))
				meta = fix_metadata(series.to_dict())
				yield (path, meta)

def sheet_to_path(sheet_name):
	"""Convert an Excel sheet name to a path segment. This will likely change for each upload batch."""
	return Path(SHEET_NAME)

def do_for_all(pairs_gen, func):
	for pair in pairs_gen:
		func(*pair)

def check_dir(path, meta):
	print("checking path: ", path.joinpath(meta[ID_COL]))
	assert path.joinpath(meta[ID_COL]).exists()

def uploader(session, count = None, test = False):
	"""
	Create and return a function that takes a path and metadata and advances an upload.
	count: int -- if not `None`, skip all but the first `count` uploads
	test: bool -- if True, upload to the IA test collection instead of as specified in the metadata
	"""
	uploaded = 0
	def process_one(path, meta):
		nonlocal uploaded
		if count is None or uploaded < count:
			if test:
				meta['collection'] = 'test_collection'
			ia_id = process_row(session, meta, path)
			print("uploaded {}".format(uploaded + 1), file = sys.stderr)
			uploaded += 1
	return process_one

get_rows = lambda: iter_excel(EXCEL_FILENAME, sheet_to_path)
with ia.get_session(config_file = CONFIG_FILENAME) as sess:
	"""
	Here are 3 `do_for_all` statements. The last one does the full real upload.
	I recommend running all three, in order, to make sure things are all set before uploading.
	"""

	# ensure all scans in the spreadsheet exist
	print("Checking if rows in the spreadsheet exist as files...")
	try:
		do_for_all(get_rows(), check_dir)
	except AssertionError:
		print("Some items in the spreadsheet don't exist")
		print("Did you remember to run mount.sh?")
		exit()
	print("Confirmed all scans in the spreadsheet exist")

	# run a test upload of one item
	#print("Starting test upload of 1 file...")
	#do_for_all(get_rows(), uploader(sess, count = 1, test = True))

	# do the real upload
	print("Starting real upload...")
	do_for_all(get_rows(), uploader(sess))
	print("Uploads complete")
