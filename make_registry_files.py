

def make_registry(base, dirs, output, recursive=True):
    from pathlib import Path
    from pooch import file_hash
    pat = '**/*' if recursive else '*'
    hashes = {p.relative_to(base).as_posix(): file_hash(str(p)) for d in dirs for p in base.joinpath(d).glob(pat) if p.is_file()}
    names = sorted(hashes.keys())
    with open(output, 'w') as outfile:
        for name in names:
            outfile.write(f'{name} {hashes[name]}\n')


def one_tag(base):
    registries = {
        'mcstas': ('mcstas-comps',),
        'mcxtrace': ('mcxtrace-comps',),
        'libc': ('common/lib/share', 'mcstas/nlib', 'mxctrace/xlib'),
    }
    for name, dirs in registries.items():
        make_registry(base, dirs, f'{name}-registry.txt')


def all_tags():
    from pathlib import Path
    import git
    repo = git.Repo(Path(__file__).parent, search_parent_directories=False)
    mccode_dir = Path(__file__).parent.joinpath('mccode')
    mccode = git.Repo(mccode_dir, search_parent_directories=False)

    tags = [tag for tag in repo.tags if str(tag).startswith('v')]
    missing = [tag for tag in mccode.tags if str(tag).startswith('v') and tag not in tags]
    for tag in missing:
        mccode.git.checkout(tag)
        one_tag(mccode_dir)
        repo.git.add('mcstas-registry.txt')
        repo.git.add('mcxtrace-registry.txt')
        repo.git.add('libc-registry.txt')
        repo.index.commit(f'Add {tag} registries')
        repo.git.tag(tag, message=f'Add {tag} registries')

    repo.remote('origin').push(tags=True)


if __name__ == '__main__':
    all_tags()