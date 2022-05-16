"""
Create a bibliography by merging all glossa publications in the repository and their references.
"""
from clldutils.path import TemporaryDirectory

from linglit.cli_util import add_provider, get_provider
from linglit.bibtex import iter_entries, iter_merged


def register(parser):
    add_provider(parser)


def run(args):
    def bibtex(src):
        return '{}\n'.format(src.bibtex())

    repos = get_provider(args)
    with TemporaryDirectory() as tmp:
        for pub in repos.iter_publications():
            with tmp.joinpath('{}.bib'.format(pub.id)).open('w') as bib:
                bib.write(bibtex(pub.as_source()))
                for src in pub.cited_references:
                    bib.write(bibtex(src))
        for src, _ in iter_merged(iter_entries(tmp)):
            print(bibtex(src))
