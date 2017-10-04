# Converts Markdown manual to man page or any other format supported by Pandoc.
# See <http://pandoc.org/> for more details.

SOURCE_DOCS := $(wildcard *.md)

EXPORTED_DOCS=\
 $(SOURCE_DOCS:.md=) \
 $(SOURCE_DOCS:.md=.html) \
 $(SOURCE_DOCS:.md=.docx) \
 $(SOURCE_DOCS:.md=.odt) \
 $(SOURCE_DOCS:.md=.tex) \
 $(SOURCE_DOCS:.md=.gz)

RM=rm -f
PANDOC=pandoc
PANDOC_OPTIONS=--smart --standalone
PANDOC_MAN_OPTIONS=--to man
PANDOC_HTML_OPTIONS=--to html5
PANDOC_DOCX_OPTIONS=--to docx
PANDOC_ODT_OPTIONS=--to odt
PANDOC_LATEX_OPTIONS=--to latex


% : %.md
	$(PANDOC) $(PANDOC_OPTIONS) $(PANDOC_MAN_OPTIONS) -o $@ $<
	gzip -k $@

%.html : %.md
	$(PANDOC) $(PANDOC_OPTIONS) $(PANDOC_HTML_OPTIONS) -o $@ $<

%.docx : %.md
	$(PANDOC) $(PANDOC_OPTIONS) $(PANDOC_DOCX_OPTIONS) -o $@ $<

%.odt : %.md
	$(PANDOC) $(PANDOC_OPTIONS) $(PANDOC_ODT_OPTIONS) -o $@ $<

%.tex : %.md
	$(PANDOC) $(PANDOC_OPTIONS) $(PANDOC_LATEX_OPTIONS) -o $@ $<


.PHONY: all clean

all : $(EXPORTED_DOCS)

clean:
	- $(RM) $(EXPORTED_DOCS)
