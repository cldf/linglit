# linglit

Programmatic access to linguistic literature

[![Build Status](https://github.com/cldf/linglit/workflows/tests/badge.svg)](https://github.com/cldf/linglit/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/linglit.svg)](https://pypi.org/project/linglit)


## Overview

`linglit` provides programmatic access to data buried in linguistic literature. Currently, this means
extracting
- bibliographies
- IGT examples

from
- books published with Language Science Press (if LaTeX sources are publicly available)
- papers published in Glossa (if XML downloads are publicly available)

`linglit` does not come with any data (except some configuration), but it provides functionality to create and
curate repositories with the "raw" data per publication provider (see [CLI](#cli)). For Language Science Press such a repository
is publicly available at https://github.com/langsci/raw_texfiles .


## Install

Install from [PyPI](https://pypi.org) with `pip`:
```shell
pip install linglit
```

Some `linglit` funtionality depends on other programs that need to be installed separately:
- Extracting data from LSP books requires [bibtool](http://www.gerd-neugebauer.de/software/TeX/BibTool/en/).
- Creating a local repository of LSP data requires [gh](https://cli.github.com/) (but this is only
  necessary if you are not happy with the content in https://github.com/langsci/raw_texfiles, which can
  simply be cloned or downloaded from a release).


## CLI

Installing the `linglit` python package will also install a commandline tool `linglit`. All functionality is
provided by subcommands. To see a list of available subcommands, run
```shell
$ linglit -h
usage: linglit [-h] [--log-level LOG_LEVEL] COMMAND ...

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        log level [ERROR|WARN|INFO|DEBUG] (default: 20)

available commands:
  Run "COMAMND -h" to get help for a specific command.

  COMMAND
    bib                 Show the bibliography of a publication
    igt                 Show the IGT examples of a publication
    update              Update a linglit data repository
```

### Downloading "raw" data

Running
```shell
linglit update <PROVIDER> <DIRECTORY>
```
will load the raw data for a provider in the existing directory `<DIRECTORY>`.


### Extracting bibliographies

Running
```shell
linglit bib <PROVIDER> <DIRECTORY> <PUBID>
```
will print the bibliography of a publication in a serialization format roughly following the Unified Stylesheet
for Linguistics.

```shell
$ linglit bib glossa ../../cldf_datasets/imtvault/raw/glossa/ 6371 
Aissen, Judith. 2003. Differential object marking: Iconicity vs. economy. Natural Language and Linguistic Theory 21. 435-483.

Ameka, Felix and de Witte, Carlien and Wilkins, David and Wilkins, David. 1999. Picture series for positional verbs: Eliciting the verbal component in locative descriptions. In Manual for the 1999 field season, 48-54. Nijmegen: Max Planck Institute for Psycholinguistics.
...
```

Using the `--bibtex` option will print out the bibliography formatted in BibTeX:
```shell
$ linglit bib glossa ../../cldf_datasets/imtvault/raw/glossa/ 6371 --bibtex
@article{glossa6371:B1,
  author  = {Aissen, Judith},
  year    = {2003},
  pages   = {435-483},
  doi     = {10.1023/A:1024109008573},
  title   = {Differential object marking: Iconicity vs. economy},
  journal = {Natural Language and Linguistic Theory},
  volume  = {21}
}

@incollection{glossa6371:B2,
  author    = {Ameka, Felix and de Witte, Carlien and Wilkins, David and Wilkins, David},
  year      = {1999},
  pages     = {48-54},
  title     = {Picture series for positional verbs: Eliciting the verbal component in locative descriptions},
  booktitle = {Manual for the 1999 field season},
  address   = {Nijmegen},
  publisher = {Max Planck Institute for Psycholinguistics}
}
...
```

### Extracting IGT examples

Running
```shell
linglit igt <PROVIDER> <DIRECTORY> <PUBID>
```
will print the IGT examples from a publication.

```shell
$ linglit igt glossa ../../cldf_datasets/imtvault/raw/glossa/ 6371 
(1) daww1239 (glossa6371: 1)
tir ka’ mãr [yeg ked/*rid/*∅)]
tir    ka’             mãr    [yeg      ked/*rid/*∅)]
3SG    lie.in.hammock  REP    [hammock  in/*LOC/*∅]
‘He was lying in the hammock [inanimate noun], they say.’ (MS, ailla:254700, 20130724_historia_McS.wav, 4:30–4:46)’

(2) daww1239 (glossa6371: 2)
‘aa’ nẽed dôo’ [baal’ rid/*ked/ *∅)]
‘aa’    nẽed    dôo’        [baal’    rid/*ked/ *∅)]
ANPH    come    AUX:source  [Manaus   LOC/*IN/*∅]
‘He came yesterday from Manaus [place name].’ (MFM, ailla:254700, 20130723_historia_MFM.wav, 6:50–7:30)’

...
```

## Python API

`linglit` provides a python API to access the content of different publication providers in a unified way. The
main point of access for data is a `Repository`. Each provider is implemented as subclass of `linglit.base.Repository`,
which can be retrieved by provider ID:
```python
>>> from linglit import PROVIDERS
>>> repo_cls = PROVIDERS['langsci']
>>> langsci = repo_cls('langsci')
>>> print(langsci['17'])
Wilbur, Joshua 2014. A grammar of Pite Saami
```

### IGT examples

Examples are modeled as instances of `linglit.base.Example`. These can be accessed as follows:
```python
>>> ex = langsci['17'].examples[10]
>>> print(ex.as_igt())
dä virtiv válldet giehpajd ja ribbrev ja dagarijd ulgos
dä    virti-v       vállde-t    giehpa-jd    ja    ribbre-v      ja    dagari-jd    ulgos
then  must-1SG.PRS  take-INF    lung-ACC.PL  and   liver-ACC.SG  and   such-ACC.PL  out
‘Then I have to take out the lungs, the liver and such things. 080909103’
```

### References

References are modeled as `pycldf.sources.Source` instances.

```python
>>> src = langsci['17'].cited_references[5]
>>> print(src)
Grundström, Harald and Väisänen, A. O. 1958. Lapska sånger: Texter och melodier från svenska Lappland (Jonas Eriksson Steggos sånger). (Skrifter utgivna genom Landsmåls- och Folkminnesarkivet i Uppsala, 1.) Uppsala: Lundequistska bokhandeln.
>>> print(src.bibtex())
@book{langsci17:grundstroem1958a,
  address   = {Uppsala},
  keywords  = {Pite, Jojk, Musicology},
  language  = {Swedish and German and Pite Saami},
  number    = {1},
  publisher = {Lundequistska bokhandeln},
  series    = {Skrifter utgivna genom Landsmåls- och Folkminne
```
