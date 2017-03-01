MAIN_FILENAME = thesis
STATEMENT_FILENAME = statement
MAIN_TEX_FILENAME = $(MAIN_FILENAME).tex
STATEMENT_TEX_FILENAME = $(STATEMENT_FILENAME).tex
BUILD_DIR = build

.PHONY: $(MAIN_FILENAME) all clean

all: $(MAIN_FILENAME)

$(MAIN_FILENAME):
	latexmk -xelatex $(STATEMENT_TEX_FILENAME) $(MAIN_TEX_FILENAME)
#	latexmk -pdf -outdir=$(BUILD_DIR) -auxdir=$(BUILD_DIR) $(STATEMENT_TEX_FILENAME) $(MAIN_TEX_FILENAME)

clean:
	latexmk -C -bibtex # bibtex to remove *.bbl files
#	latexmk -outdir=$(BUILD_DIR) -auxdir=$(BUILD_DIR) -C -bibtex # bibtex to remove *.bbl files
	rm -f "$(MAIN_FILENAME).glsdefs" "$(MAIN_FILENAME).run.xml" # those are not handled by latexmk -C
#	rm -f "$(BUILD_DIR)/$(MAIN_FILENAME).glsdefs" "$(BUILD_DIR)/$(MAIN_FILENAME).run.xml" # those are not handled by latexmk -C
