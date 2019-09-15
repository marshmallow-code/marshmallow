# Releasing

1. Bump version in `src/marshmallow/__init__.py` and update the changelog
   with today's date.
2. Commit:  `git commit -m "Bump version and update changelog"`
3. Tag the commit: `git tag x.y.z`
4. Push: `git push --tags origin dev`. CI will take care of the
   PyPI release.
5. Add release notes on Tidelift.
