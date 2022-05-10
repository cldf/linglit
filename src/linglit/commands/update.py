"""
Update a linglit data repository
"""
from clldutils.clilib import PathType

from linglit import PROVIDERS


def register(parser):
    parser.add_argument('provider', choices=list(PROVIDERS.keys()))
    parser.add_argument('dir', type=PathType(type='dir'))


def run(args):
    repo = PROVIDERS[args.provider](args.dir)
    repo.create(verbose=True)
