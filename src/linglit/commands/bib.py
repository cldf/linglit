"""
Show the bibliography of a publication
"""
from linglit.cli_util import add_publication, get_publication


def register(parser):
    add_publication(parser)
    parser.add_argument('--bibtex', action='store_true', default=False)


def run(args):
    for src in get_publication(args).cited_references:
        print(src.bibtex() if args.bibtex else src)
        print('')
