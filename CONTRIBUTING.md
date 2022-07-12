
# Contributing to `linglit`

## Parser updates

`linglit`'s data extraction capabilities depend on typographic conventions used in the source
publications. Thus, parsing may break when these conventions change. Since you may be the first
person running `linglit` on a brand new Glossa paper or Language Science Press book, you may also
be the first one to encounter such breakage.
Llet us know](https://github.com/cldf/linglit/issues/new).


## New data providers

If you know of a linguistic publication (a journal or an archive for example) which publishes
- IGT examples and/or bibliographies or reference lists
- under an open license
- in a format that is structured enough to allow for automated extraction

[let us know](https://github.com/cldf/linglit/issues/new).


## IGT language identification

Due to the diverity of typographic conventions to indicate an IGT example's language
(for both, `glossa` and `langsci`), detecting this language is a sketchy and imprecise process.

To guide this process, `linglit` can make use of extra information, though. For `langsci` books
on individual languages (typically grammars or dictionaries), this language (if indicated in the
`langsci` catalog) is taken as default. But sometimes, books have individual chapters devoted to a
single language. Such cases can be indicated in 
[the linglit configuration](src/linglit/cfg/langsci/texfile_titles.tsv), mapping filenames of the
LaTeX files containing the chapter to a language name.

A similar mechanism exists [for glossa](src/linglit/cfg/glossa/glossa.csv), mapping `glossa` article
numbers to example languages specified by Glottocode.

If you find Glossa papers or Language Science Press chapters missing in these lists,
[let us know](https://github.com/cldf/linglit/issues/new).


## Contributing to the `linglit` codebase

1. Fork `cldf/linglit`
2. Clone your fork
3. Install `linglit` for development (preferably in a separate virtual environment) running
   ```shell
   pip install -r requirements.txt
   ```
4. Run the tests
   ```shell
   pytest
   ```
