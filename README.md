# Pooch registry files for McStas/McXtrace
Trialing solution 2 for https://github.com/mccode-dev/McCode/issues/1529


## Tips for local development
Clone this repository, e.g.,
```bash
git clone https://github.com/g5t/mccode-pooch.git mccode_pooch
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
(venv) $ python make_registry_files.py
```