"""
Update a linglit data repository
"""
from linglit.cli_util import add_provider, get_provider


def register(parser):
    add_provider(parser)


def run(args):  # pragma: no cover
    repo = get_provider(args)
    repo.create(verbose=True)
