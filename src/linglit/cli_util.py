from clldutils.clilib import PathType

from linglit import PROVIDERS


def add_provider(parser):
    parser.add_argument('provider', choices=list(PROVIDERS.keys()))
    parser.add_argument('dir', type=PathType(type='dir'))


def get_provider(args):
    return PROVIDERS[args.provider](args.dir)


def add_publication(parser):
    add_provider(parser)
    parser.add_argument('pubid')


def get_publication(args):
    return get_provider(args)[args.pubid]
