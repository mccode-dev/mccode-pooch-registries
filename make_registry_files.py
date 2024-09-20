def make_registry(base, dirs, output, recursive=True):
    from pooch import file_hash
    pat = '**/*' if recursive else '*'
    hashes = {p.relative_to(base).as_posix(): file_hash(str(p)) for d in dirs for p in base.joinpath(d).glob(pat) if p.is_file()}
    names = sorted(hashes.keys())
    with open(output, 'w') as outfile:
        for name in names:
            outfile.write(f'{name} {hashes[name]}\n')


def make_registries(repo, base, message):
    registries = {
        'mcstas': ('mcstas-comps',),
        'mcxtrace': ('mcxtrace-comps',),
        'libc': ('common/lib/share', 'mcstas/nlib', 'mcxtrace/xlib'),
    }
    for name, dirs in registries.items():
        registry_name = f'{name}-registry.txt'
        make_registry(base, dirs, registry_name)
        repo.git.add(registry_name)
    repo.index.commit(message)


def one_tag(repo, base, mccode, tag):
    mccode_current = mccode.active_branch
    repo_current = repo.active_branch

    mccode.git.checkout(tag)
    message = f'Add {tag} registries'
    make_registries(repo, base, message)
    # repo.git.tag(tag, message=message)
    repo.create_tag(tag, message=message)

    mccode.git.checkout(mccode_current.name)
    repo.git.checkout(repo_current.name)


def one_branch(repo, base, mccode, name, push: bool):
    if name not in mccode.branches:
        return
    mccode_current = mccode.active_branch
    mccode.git.checkout(name)

    repo_current = repo.active_branch
    if name in repo.branches:
        repo.git.checkout(name)
    else:
        repo.git.checkout('-b', name)
        repo.git.branch('-u', 'origin', name)

    make_registries(repo, base, f'Add {name} branch registries')

    if push:
        repo.remote('origin').push()

    mccode.git.checkout(mccode_current.name)
    repo.git.checkout(repo_current.name)


def do_everything(push: bool):
    from pathlib import Path
    import git
    repo = git.Repo(Path(__file__).parent, search_parent_directories=False)
    mccode_dir = Path(__file__).parent.joinpath('mccode')
    mccode = git.Repo(mccode_dir, search_parent_directories=False)

    tags = [tag for tag in repo.tags if str(tag).startswith('v')]
    missing = [tag for tag in mccode.tags if str(tag).startswith('v') and tag not in tags]
    for tag in missing:
        print(f'handle missing tag {tag}')
        one_tag(repo, mccode_dir, mccode, tag)

    # Also track special branches:
    for branch in ("main",):
        one_branch(repo, mccode_dir, mccode, branch, push=push)

    if push:
        repo.remote('origin').push(tags=True)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser('make_registry_files')
    parser.add_argument('-n', '--no-push', action='store_true', default=False)
    args = parser.parse_args()

    do_everything(push=not args.no_push)
