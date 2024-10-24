"""
Create a bibliography by merging all glossa publications in the repository and their references.
"""
from clldutils.path import TemporaryDirectory
from tqdm import tqdm
from pybtex.database import parse_string

from linglit.cli_util import add_provider, get_provider
from linglit.bibtex import iter_entries, iter_merged


def register(parser):
    add_provider(parser)
    parser.add_argument(
        '--drop-until', type=int, help='Numeric ID of the first book to process.', default=None)


def run(args):
    def bibtex(src):
        return '{}\n'.format(src.bibtex())

    repos = get_provider(args)
    do = False if args.drop_until else True
    with TemporaryDirectory() as tmp:
        for pub in tqdm(repos.iter_publications()):
            if pub.id == 'langsci{}'.format(args.drop_until):
                do = True
            if not do:
                continue
            with tmp.joinpath('{}.bib'.format(pub.id)).open('w') as bib:
                bib.write(bibtex(pub.as_source()))
                for src in pub.cited_references:
                    bib.write(bibtex(src))
        ids = set()
        for src, _ in iter_merged(iter_entries(tmp)):
            src.id = src.id.replace('\\', '')
            assert src.id not in ids, src.id
            ids.add(src.id)
            res = bibtex(src)
            parse_string(res, 'bibtex')
            print(res)
