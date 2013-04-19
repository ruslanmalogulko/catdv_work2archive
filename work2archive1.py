#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
1. Reading from .txt file strings with path of each file for move.
2. Creating a new path name for each file according to destination place.
3. If destination folder does not exists - create it.
4. After all - trying to move file with path from list to destination place (if file does not 
	appear in that folder earlier, in this case leave file in previous place with writing 
	a correct messate to log file).
"""


import os
import sys
import time
import logging
import MySQLdb
import logging.handlers
import datetime
import shutil
import codecs
from PyRTF import *
# from rtfng import *
# from rtfng import Elements, Renderer, Styles, utils, Constants, PropertySets
# from rtfng.document import section, paragraph

# sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


log=logging.getLogger('main') 
log.setLevel(logging.DEBUG) 
formatter=logging.Formatter('%(asctime)s.%(msecs)d %(levelname)s in \'%(module)s\' at \
	line %(lineno)d: %(message)s','%Y-%m-%d %H:%M:%S') 
# handler = TimedCompressedRotatingFileHandler('/var/log/videowf/folder_monitor.log', when='midnight', interval=1)
handler=logging.FileHandler('testlog.log', 'a') 
handler.setFormatter(formatter)
# handler.setLevel(logging.DEBUG)
log.addHandler(handler) 

# logging.basicConfig(filename="testlog.log", 
#                     format=formatter, level=logging.DEBUG)

log.info('\n'*3 + ' '*5 + '*'*50)
# log.info('-'*50)
log.info(datetime.datetime.now())
# log.info('-'*50)
log.info("---Start log---")


args = sys.argv 																# get arguments 
path_list = [] 																	# a variable for list extracted form txt file
dest_folder = '/home/russel/_dev/py/cat_dv/catdv_work2archive/archive/media' 	# destination folder for copied files


dbcatdvname = 'catdv'
dbcatdvip = '172.22.64.156'
dbcatdvpass = 'Impo$$iblecatdv'
dbcatdvuser = 'catdv'
catdv_selector = "SELECT clip.id, clip.notes FROM clip WHERE clip.catalogID='1504'"


# Check destination folder existing and fix name (if without end "/"")
def check_destfolder(dest_folder):
	print dest_folder
	if os.path.exists(dest_folder):
		if os.path.isdir(dest_folder):
			if dest_folder.split('/')[-1]!='':
				dest_folder += '/'
			log.info("Destination folder exists and OK: %s" % dest_folder)
	else:
		log.info("Destination folder doesn't exists. Creating...")
		try:
			create_folder(dest_folder)
		except Exception, e:
			log.error("The error occured while creating destination folder: %s" % e[1])
		else:
			log.info("Destination folder created!")


# Check for existing file in destination folder
def check_dest_file(filename):
	if os.path.exists(filename):
		return True
	else:
		return False


# Create dest folder if does not exists
def create_folder(dest_folder):
	os.makedirs(dest_folder)
		

# Get path-list from txt file to array
def get_path_list(f):
	paths = f.readlines()
	for line in paths:
		if len(line)!=0:
			if line[-1].find('\n')!=-1:
				path_list.append(line[:-1])
			else:
				path_list.append(line)
	log.info("Path list from txt: %s" % path_list)


# Try to open txt file. Its path was sent as argument
def open_txt():
	try:
		f = open(args[1], 'r')
	except Exception as e:
		log.error("The error occured while opening txt file: %s" % e[1])
	else:
		get_path_list(f)
	finally:
		f.close()


# Try move file
def move_file(filename):
	new_filename = make_new_name(filename, '/archive/media', '/work') 		#making new path 
	log.info("The new filename created: %s " % new_filename)
	check_destfolder(new_filename[:new_filename.rfind('/')]) 				#cheking destination folder
	if check_dest_file(new_filename)==False:
		try:
			shutil.move(filename, new_filename)
		except Exception, e:
			log.error("The error occured while moving file: %s" % e[1])
		else:
			log.info("And file moved successfully!")
	else:
		log.error("The filename: %s exists in destination folder already! Skip moving!" % new_filename)


# Make new filename with proper destination. new_part='archive/media', old_part='/work' in our case
def make_new_name(filename, new_part, old_part):
	new_filename = filename[:filename.find(old_part)]+new_part+filename[filename.find(old_part)+
																		len(old_part):]
	# print new_filename
	return new_filename


# Create .rtf file
def make_rtf(sql_results):
	doc = Document()
	ss = doc.StyleSheet
	sec = Section()
	doc.Sections.append(sec)

	edge = BorderPS(width=20, style=BorderPS.SINGLE)
	frame = FramePS(edge, edge, edge, edge)

	p = Paragraph(ss.ParagraphStyles.Heading1)
	p.append('catalog id = 1504')
	sec.append(p)

	table = Table(TabPS.DEFAULT_WIDTH*3, TabPS.DEFAULT_WIDTH*7)
	# 

	for row in sql_results:
		c1 = Cell(Paragraph(ss.ParagraphStyles.Normal, ParagraphPS(alignment=3), rtf_encode(str(row[0]))), frame)
		row1 = ''
		if type(row[1]) is unicode:
			# row1 = unicode(row[1]).encode('utf8', 'ignore')

			row1 = rtf_encode(row[1])
			# row1 = row[1]
			# row1 = row[1].encode('utf8', 'ignore')
			# .decode('utf8').encode('latin')
			# .encode('urf8', 'ignore')
			# .decdde('utf8', 'ignore')
		else:
			row1 = ''
		print row1
		c2 = Cell(Paragraph(ss.ParagraphStyles.Normal, str(row1)), frame)
		if row1!='':
			table.AddRow(c1, c2)

	sec.append(table)
	DR = Renderer()
	DR.Write(doc, open_file('test1'))


# Encode string to utf8
def rtf_encode(unistr):
    return ''.join([c if ord(c) < 128 else u'\\u' + unicode(ord(c)) + u'?' for c in unistr])


def open_file(name):
	return file('%s.rtf' % name, 'w')


def sql_get(catdv_selector, dbcatdvip, dbcatdvuser, dbcatdvpass, dbcatdvname):
	try:
		db_catdv = MySQLdb.connect(dbcatdvip, dbcatdvuser, dbcatdvpass, dbcatdvname, charset = "utf8", use_unicode=True)
	except Exception, e:
		log.error("Error in connection to database: %s" % e)
	else:
		cursor_catdv = db_catdv.cursor()
		try:
			cursor_catdv.execute(catdv_selector)
		except Exception, e:
			log.error("Error in cursor executing: %s" % e)
			db_catdv.rollback()
		else:
			db_catdv.commit()
			results = cursor_catdv.fetchall()
			# for row in results:
				# print str(row[1]).encode('utf-8').strip()
				# if type(row[1]) is unicode:
					# print unicode(row[1]).encode('utf8', 'ignore')
	return results


# Check the number of args and read .txt file with filepaths
def init():
	if len(args) == 2: 														#if received .txt file as argument
		log.info("There are one argument received.")
		if args[1].find('.txt') != -1: 										#if not .txt file received as argument
			log.info("And it is txt object.")
			open_txt()
			for path in path_list:
				move_file(path) 											#starting move procedure for each path string in .txt file
		else:
			log.error("There not txt object as argument received.")
	else:
		log.error("The number of argument seems doesn't proper: %d items" % (len(args)-1))


def main():
	# init()
	sql_results = sql_get(catdv_selector, dbcatdvip, dbcatdvuser, dbcatdvpass, dbcatdvname)
	make_rtf(sql_results)

if __name__ == '__main__':
	main()


log.info("---End log at %s---\n" %datetime.datetime.now())
log.info('\n' + ' '*5 + '*'*50)