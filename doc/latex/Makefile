MAIN_FILENAME = thesis
MAIN_TEX_FILENAME = $(MAIN_FILENAME).tex
STATEMENT_FILENAME = statement
STATEMENT_TEX_FILENAME = $(STATEMENT_FILENAME).tex
ABSTRACT_PL_SEPARATE_FILENAME = abstract-pl-separate
ABSTRACT_PL_SEPARATE_TEX_FILENAME = $(ABSTRACT_PL_SEPARATE_FILENAME).tex
ABSTRACT_ENG_SEPARATE_FILENAME = abstract-eng-separate
ABSTRACT_ENG_SEPARATE_TEX_FILENAME = $(ABSTRACT_ENG_SEPARATE_FILENAME).tex
TITLE_PAGE = strona-tytulowa
BUILD_DIR = build

.PHONY: $(MAIN_FILENAME) all clean

all: $(MAIN_FILENAME) $(ABSTRACT_PL_SEPARATE_FILENAME) $(ABSTRACT_ENG_SEPARATE_FILENAME)

$(MAIN_FILENAME):
	latexmk -xelatex $(STATEMENT_TEX_FILENAME) $(MAIN_TEX_FILENAME)
#	latexmk -pdf -outdir=$(BUILD_DIR) -auxdir=$(BUILD_DIR) $(STATEMENT_TEX_FILENAME) $(MAIN_TEX_FILENAME)
#	Make PDF smaller - see: https://tex.stackexchange.com/questions/18987/how-to-make-the-pdfs-produced-by-pdflatex-smaller
#	gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=foo-compressed.pdf foo.pdf
	pdftk $(MAIN_FILENAME).pdf cat 1 output $(TITLE_PAGE).pdf

$(ABSTRACT_PL_SEPARATE_FILENAME):
	latexmk -pdf $(ABSTRACT_PL_SEPARATE_TEX_FILENAME)

$(ABSTRACT_ENG_SEPARATE_FILENAME):
	latexmk -pdf $(ABSTRACT_ENG_SEPARATE_TEX_FILENAME)

clean:
	latexmk -C -bibtex # bibtex to remove *.bbl files
#	latexmk -outdir=$(BUILD_DIR) -auxdir=$(BUILD_DIR) -C -bibtex # bibtex to remove *.bbl files
	rm -f "$(MAIN_FILENAME).glsdefs" "$(MAIN_FILENAME).run.xml" *.fls *.log # those are not handled by latexmk -C
#	rm -f "$(BUILD_DIR)/$(MAIN_FILENAME).glsdefs" "$(BUILD_DIR)/$(MAIN_FILENAME).run.xml" # those are not handled by latexmk -C
