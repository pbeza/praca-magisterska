#!/usr/bin/env python3

import os
import re

mistakes_found = False

def print_line_matches(line, line_no, fpath, hardspaces_regex, labels_regex):
	global mistakes_found
	whitespaces_match = hardspaces_regex.search(line)
	labels_match = labels_regex.search(line)

	if whitespaces_match or labels_match:
		if mistakes_found == False:
			print("--------------------------------------------------------\n")
			print("MISTAKES IN FILE '" + fpath + "':\n")
		mistakes_found = True
		if whitespaces_match:
			print("      Match '" + str(whitespaces_match.group(0)) + "' in line " + str(line_no) + ":")
		if labels_match:
			print("      Match '" + str(labels_match.group(0)) + "' in line " + str(line_no) + ":")
		print("      Line: '" + line.strip() + "'\n")

def print_latex_mistakes(fpath, hardspaces_regex, labels_regex):
	global mistakes_found
	line_no = 0
	mistakes_found = False

	with open(fpath) as f:
		for line in f:
			line_no = line_no + 1
			if line.strip().startswith("%"):
				continue
			print_line_matches(line, line_no, fpath, hardspaces_regex, labels_regex)

def add_regex_on_sides(s):
#	xstr = '[^\w~]'
	xstr = '\s'
	return xstr + s + xstr

def get_hardspaces_regex():
	keywords = [ 'a', 'ci', 'co', 'do', 'gdy', 'i', 'lub', 'm.in.', 'nad', 'np.', 'o', 'oraz', 'pod', 'przy', 'u', 'ta', 'to', 'tzn.', 'w', 'z', 'za', 'ze', 'że' ]
	keywords_extended = [ add_regex_on_sides(s) for s in keywords ]
	wregex = '(' + '|'.join(keywords_extended) + ')'
	print("Whitespaces regex for all the '*" + file_extension + "' files:")
	print("'" + wregex + "'\n")
	return re.compile(wregex)

def get_unqualified_labels_regex():
	lregex = r'.*((\\label|\\ref){(?!.*(ch:|sec:|subsec:|fig:|tab:|eq:|lst:|itm:|alg:|app:)).*}.*)'
	print("Labels regex for all the '*" + file_extension + "' files:")
	print("'" + lregex + "'\n")
	return re.compile(lregex)

if __name__ == '__main__':
	rootdir = '.'
	file_extension = '.tex'

	hardspaces_regex = get_hardspaces_regex()
	labels_regex = get_unqualified_labels_regex()

	for root, _, files in os.walk(rootdir):
		for f in files:
			if f.endswith(file_extension):
				fpath = os.path.join(root, f)
				print_latex_mistakes(fpath, hardspaces_regex, labels_regex)
