#!/usr/bin/env python3

import os
import re

mistakes_found = False

def print_line_matches(line, line_no, fpath, regex):
	global mistakes_found
	match = regex.search(line)

	if match:
		if mistakes_found == False:
			print("--------------------------------------------------------\n")
			print("MISTAKES IN FILE '" + fpath + "':\n")
		mistakes_found = True
		print("      Match '" + str(match.group(0)) + "' in line " + str(line_no) + ":")
		print("      Line: '" + line.strip() + "'\n")

def print_latex_mistakes(fpath, regex):
	global mistakes_found
	line_no = 0
	mistakes_found = False

	with open(fpath) as f:
		for line in f:
			line_no = line_no + 1
			if line.strip().startswith("%"):
				continue
			print_line_matches(line, line_no, fpath, regex)

def add_regex_on_sides(s):
	return xstr + s + xstr

if __name__ == '__main__':
	rootdir = '.'
	file_extension = '.tex'
	keywords = [ 'a', 'ci', 'co', 'do', 'gdy', 'i', 'lub', 'm.in.', 'nad', 'np.', 'o', 'oraz', 'pod', 'przy', 'u', 'ta', 'to', 'tzn.', 'w', 'z', 'za', 'ze', 'że' ]
#	xstr = '[^\w~]'
	xstr = '\s'
	keywords_extended = [ add_regex_on_sides(s) for s in keywords ]
	regex = '(' + '|'.join(keywords_extended) + ')'

	print("Regex for all the '*" + file_extension + "' files: '" + regex + "'\n")

	regex = re.compile(regex)

	for root, _, files in os.walk(rootdir):
		for f in files:
			if f.endswith(file_extension):
				fpath = os.path.join(root, f)
				print_latex_mistakes(fpath, regex)
