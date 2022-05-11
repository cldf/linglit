"""
Show the IGT examples of a publication
"""
from linglit.cli_util import add_publication, get_publication


def register(parser):
    add_publication(parser)


def run(args):
    for ex in get_publication(args).examples:
        print(ex)
        print('')
