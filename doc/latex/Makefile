NAME         = 'praca_magisterska'
PDF_FILENAME = $(NAME).pdf
TEX_FILENAME = $(NAME).tex

.PHONY: $(PDF_FILENAME) all clean

all: $(PDF_FILENAME)

$(PDF_FILENAME):
	latexmk -pdf $(TEX_FILENAME)

clean:
	latexmk -C -bibtex # bibtex to remove *.bbl files
	rm -f $(NAME).glsdefs $(NAME).run.xml # those are not handled by latexmk -C
