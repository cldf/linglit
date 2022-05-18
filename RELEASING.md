# Releasing linglit

* run tests via tox and flake8 (making sure statement coverage is at 100%):
```shell
tox -r
flake8 src
```

* Change to the new  version number in `setup.cfg`

- Create a release tag:
```shell
git tag -a v<VERSION> -m "<VERSION> release"
```

* Release to PyPI:
```shell
rm dist/*
python -m build
twine upload dist/*
```

* Push to GitHub:
```shell
git push origin
git push --tags origin
```
