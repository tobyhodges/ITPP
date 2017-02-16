#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

DESCRIPTION

    Generate PDF handout from multiple iPython/Jupyter Notebooks
    - iterates over all .ipynb notebooks in current directory 
    - extracts the JSON content
    - merges it into a single file
    - calls jupyter nbconvert to generate a latex file
    - tweaks the resulting latex file
    - calls pdflatex to compile the latex file into pdf
    - calls pdfjoin to merge a title page to the front

AUTHOR

    Holger Dinkel <dinkel@embl.de>

"""
VERSION='0.1'


import sys
import os
import traceback
import json
import glob
import optparse 
import subprocess 
import re

def main ():

    global options, args

    all_json = None
    out_filename = os.path.basename(os.getcwd()) + '_handout.ipynb'
    tex_filename = os.path.splitext(out_filename)[0] + '.tex'
    pdf_filename = os.path.splitext(out_filename)[0] + '.pdf'
#    pdf_cheatsheet_filename = 'CheatSheet.pdf'
    title_pdf_filename = os.path.basename(os.getcwd()) + '_title.pdf'

# Combine all ipynb notebooks into one (merge JSON 'cells'):
    for filename in sorted(glob.glob('*.ipynb')):
        if filename == out_filename:
            continue
        print("Reading ipython notebook '%s'" % filename)
        with open(filename, 'r') as json_file:
            json_str = json_file.read()
        j = json.loads(json_str)
        if not all_json:
            all_json = j
        else:
            for i in j['cells']:
                all_json['cells'].append(i)

    with open(out_filename, 'w') as outfile:
        json.dump(all_json, outfile, indent=1, sort_keys=True)

    subprocess.check_call("jupyter nbconvert --execute --allow-errors --to=latex %s" % out_filename, shell=True)

    with open(tex_filename, 'r') as texfile:
        tex = texfile.read()

    tex = re.sub("\\\section\{.*?\}", "", tex, flags=re.DOTALL)  # Delete all sections (would be duplicate)
    tex = re.sub("\\\subsection\{(\d+\. )?", "\\\chapter{", tex) # rename numbered subsections to chapters
    tex = re.sub("\\\documentclass\[(\d+pt)\]\{.*?\}", "\\\documentclass[\\1]{report}", tex) # change documentclass to report
    tex = re.sub("\\\maketitle", "\\\\tableofcontents", tex) # include tableof

    with open(tex_filename, 'w') as texfile:
        texfile.writelines(tex)

    subprocess.call("pdflatex -interaction=nonstopmode %s" % tex_filename, shell=True)

    pdf_joined_filename = os.path.splitext(pdf_filename)[0] + '-joined.pdf'

    if not os.path.isfile(pdf_filename):
        print("PDF file '%s' does not exist! Stopping." % pdf_filename)
        sys.exit(1)
    elif not os.path.isfile(title_pdf_filename):
        print("PDF file '%s' does not exist! Stopping." % title_pdf_filename)
        sys.exit(1)
    else:
#        subprocess.call("pdfjoin --paper a4paper --no-landscape --twoside --rotateoversize false --outfile %s %s %s %s"% (pdf_joined_filename, title_pdf_filename, pdf_filename, pdf_cheatsheet_filename ), shell=True)
        subprocess.call("pdfjoin --paper a4paper --no-landscape --twoside --rotateoversize false --outfile %s %s %s" % (pdf_joined_filename, title_pdf_filename, pdf_filename), shell=True)
    print(pdf_joined_filename )
    if os.path.isfile(pdf_joined_filename):
        print("\n\nPDF file '%s' was generated...\n\n" % pdf_joined_filename)
        sys.exit(0)
    else:
        print("\n\nPDF file '%s' was not generated! See error messages above for details...\n\n" % pdf_joined_filename)
        sys.exit(1)


if __name__ == '__main__':
    try:
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version=VERSION)
        parser.add_option ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        (options, args) = parser.parse_args()
        main()
        sys.exit(0)
    except Exception as e:
        print('ERROR, UNEXPECTED EXCEPTION')
        print(str(e))
        traceback.print_exc()
        os._exit(1)

