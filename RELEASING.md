# Releasing

1. Bump version in `src/marshmallow/__init__.py` and update the changelog
   with today's date.
2. Commit:  `git commit -m "Bump version and update changelog"`
3. Tag the commit: `git tag x.y.z`
4. Push: `git push --tags origin dev`. TravisCI will take care of the
   PyPI release.
5. If it's a 3.0 pre-release, merge `dev` into `3.0` and push.

```
git checkout 3.0
git merge dev
git push origin 3.0
```

6. Add release notes on Tidelift.
