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
