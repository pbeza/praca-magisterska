NAME         = 'praca_magisterska'
PDF_FILENAME = $(NAME).pdf
TEX_FILENAME = $(NAME).tex

.PHONY: $(PDF_FILENAME) all clean

all: $(PDF_FILENAME)

$(PDF_FILENAME):
	latexmk -pdf $(TEX_FILENAME)

clean:
	latexmk -C
