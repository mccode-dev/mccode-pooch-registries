# Pooch registry files for McStas/McXtrace

## Tips for local development
Clone this repository, e.g.,
```bash
git clone https://github.com/mccode-dev/mccode-pooch-registries.git mccode_pooch
```

Clone the McCode repository inside of this one, e.g.,
```bash
cd mccode_pooch
git clone https://github.com/mccode-dev/McCode.git mccode
```

Setup a local development environment
```cmd 
$ python -m pip install --upgrade pip virtualenv
$ python -m virtualenv venv
$ . venv/bin/activate
(venv) $ python -m pip install -r requirements.txt 
```

Run the registry script, which will attempt to push results back to GitHub
```bash
(venv) $ python register.py --parent mccode
```
Use `-n`/`--no-push` to inspect the result before it leaves your machine.

### Re-minting existing tags
The positional `tag` argument only *adds* tags this repository does not yet have.
To re-mint tags that already exist, name them explicitly:
```bash
(venv) $ python register.py --parent mccode -n --rebuild v3.5.31 --rebuild v3.6.0
(venv) $ python register.py --parent mccode -n --rebuild-from-file tags.txt
```
Re-minting rewrites those tags, so publishing them needs
`git push origin --force-with-lease --tags`. Previous tag commits are recorded in
`.registry-tags.json` for recovery.

### A note on the source checkout
`register.py` now checks out each tag with `--force` and runs `git clean -xdf` in
the source repository before hashing. Without that, a plain `git checkout` leaves
untracked files in place and they get hashed into the registry -- which is how
`mcstas-comps/optics/Collimator_linear.comp.json`, an mccode-antlr IR sidecar
present in no McCode commit, was published in 101 tags (v3.4.0 through v3.7.6)
and made `mccode-antlr cache populate` fail for every one of them.

**The clean is destructive.** Point `--parent` at a clone kept for this purpose,
never at a checkout holding work you care about.
