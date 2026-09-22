from pathlib import Path
import json

from mccode_antlr.cli.cache import cache_register


def load_tag_snapshots(repo_path: Path):
    """Load tag→commit mappings for recovery."""
    snapshot_file = repo_path / '.registry-tags.json'
    if snapshot_file.exists():
        with open(snapshot_file) as f:
            return json.load(f)
    return {}


def save_tag_snapshots(repo_path: Path, snapshots: dict):
    """Save tag→commit mappings for recovery."""
    snapshot_file = repo_path / '.registry-tags.json'
    with open(snapshot_file, 'w') as f:
        json.dump(snapshots, f, indent=2)


def restore_tag(repo, tag: str, commit_hash: str):
    """Restore a tag to a previous commit (for recovery from failed rebuild)."""
    try:
        if tag in repo.tags:
            repo.delete_tag(tag)
        repo.create_tag(tag, ref=commit_hash)
        print(f'Restored {tag} to {commit_hash[:8]}')
    except Exception as e:
        print(f'ERROR restoring {tag}: {e}')
        raise


def make_registries(repo, base, message):
    registries = {
        'mcstas': ('mcstas-comps',),
        'mcxtrace': ('mcxtrace-comps',),
        'libc': ('common/lib/share', 'mcstas/nlib', 'mcxtrace/xlib', 'mccode/nlib', 'mccode/xlib'),
        'codegen': ('mccode/src',),
    }
    for name, dirs in registries.items():
        registry_name = f'{name}-registry.txt'
        # mccode-antlr owns this: it is the consumer of these registries, and it
        # is the only thing that knows which files it generates and so must never
        # be registered. Output is byte-identical to the hand-rolled version this
        # replaced.
        cache_register(root=str(base), dirs=list(dirs), out=registry_name)
        repo.git.add(registry_name)
    repo.index.commit(message)


def one_tag(repo, base, source, tag, rebuild=False):
    old_commit = None
    if rebuild and tag in repo.tags:
        old_commit = str(repo.tags[str(tag)].commit)
        repo.delete_tag(tag)
        print(f'Deleted existing tag {tag} (was at {old_commit[:8]})')
    
    source_ref = source.head.commit
    repo_ref = repo.head.commit

    # Check out *and clean*. A plain checkout leaves untracked files in place, so
    # anything a previous run (or a stray tool invocation) dropped into the source
    # tree gets hashed into the registry and stays there for every later tag. That
    # is how mcstas-comps/optics/Collimator_linear.comp.json -- an mccode-antlr IR
    # sidecar that exists in no McCode commit -- ended up in 101 published tags.
    source.git.checkout(tag, force=True)
    source.git.clean('-xdf')
    message = f'Add {tag} registries'
    make_registries(repo, base, message)
    repo.create_tag(tag, message=message)
    
    new_commit = str(repo.tags[str(tag)].commit)
    
    source.git.checkout(source_ref)
    repo.git.checkout(repo_ref)
    
    return {'old': old_commit, 'new': new_commit}


def v_tags(repo):
    return [tag for tag in repo.tags if str(tag).startswith('v')]


def do_everything(repo, parent, source, tag: str, rebuild_all=False, rebuild_tags=None):
    repo_path = Path(repo.working_dir)
    
    if rebuild_all or rebuild_tags:
        if rebuild_all:
            repo_tags = v_tags(repo)
        else:
            known = {str(t) for t in v_tags(repo)}
            unknown = [t for t in rebuild_tags if t not in known]
            if unknown:
                raise ValueError(f'Cannot rebuild tags this repository does not have: {unknown}')
            repo_tags = list(rebuild_tags)
        print(f'Rebuilding {len(repo_tags)} existing tags: {repo_tags}')
        snapshots = load_tag_snapshots(repo_path)
        
        for t in repo_tags:
            try:
                print(f'Handle rebuild {t=}')
                result = one_tag(repo, parent, source, str(t), rebuild=True)
                
                if str(t) not in snapshots:
                    snapshots[str(t)] = []
                snapshots[str(t)].append(result)
                print(f'  → {result["old"][:8] if result["old"] else "new"} → {result["new"][:8]}')
            except Exception as e:
                print(f'  ERROR rebuilding {t}: {e}')
                print(f'  Snapshot file saved for recovery at {snapshots}')
                save_tag_snapshots(repo_path, snapshots)
                raise
        
        save_tag_snapshots(repo_path, snapshots)
        repo.git.add('.registry-tags.json')
        return len(repo_tags) > 0
    else:
        source_tags = [tag] if tag else v_tags(source)
        repo_tags = v_tags(repo)
        missing = [t for t in source_tags if t not in repo_tags]
        # missing holds source-defined tag(s) that this repo does not have
        for tag in missing:
            print(f'Handle missing {tag=}')
            result = one_tag(repo, parent, source, tag)
            snapshots = load_tag_snapshots(repo_path)
            if tag not in snapshots:
                snapshots[tag] = []
            snapshots[tag].append(result)
            save_tag_snapshots(repo_path, snapshots)
            repo.git.add('.registry-tags.json')
        return len(missing) > 0


def main(parent: Path, push: bool, remove: bool, tag: str, rebuild_all: bool, rebuild_tags=None):
    import git
    repo = git.Repo(Path(__file__).parent, search_parent_directories=False)
    changed = False
    if remove and tag in repo.refs:
        repo.delete_tag(tag)
        if push:
            print(f'Push removed tag {tag} to origin')
            repo.remote('origin').push(refspec=f':{tag}')
    elif not remove:
        source = git.Repo(parent, search_parent_directories=False)
        if do_everything(repo, parent, source, tag, rebuild_all=rebuild_all,
                         rebuild_tags=rebuild_tags) and push:
            print(f'Push tags to origin')
            try:
                repo.remote('origin').push(tags=True)
            except git.GitCommandError as e:
                if 'failed to push' in str(e).lower() or 'rejected' in str(e).lower():
                    print(f'\nERROR: Push rejected (tags already exist on remote)')
                    print(f'\nTo overwrite remote tags with updated ones, run:')
                    print(f'  git push origin --force-with-lease --tags')
                    print(f'\nOr to force unconditionally:')
                    print(f'  git push origin --force --tags')
                else:
                    raise
        

if __name__ == '__main__':
    from argparse import ArgumentParser
    from pathlib import Path
    parser = ArgumentParser('register')
    parser.add_argument('-n', '--no-push', action='store_true', default=False)
    parser.add_argument('--parent', type=str, default=None, help='Parent repository directory to register')
    parser.add_argument('--remove', type=int, nargs='?', help='Remove the specified tag, otherwise add/update')
    parser.add_argument('--rebuild-all', action='store_true', default=False, help='Rebuild all existing tags with current registry files')
    parser.add_argument('--rebuild', action='append', default=None, metavar='TAG',
                        help='Rebuild this existing tag (repeatable). Unlike the positional '
                             'tag, which only adds tags this repository lacks, this re-mints '
                             'a tag that already exists.')
    parser.add_argument('--rebuild-from-file', type=str, default=None, metavar='FILE',
                        help='Rebuild every tag named in FILE, one per line (combines with --rebuild)')
    parser.add_argument('tag', type=str, nargs='?', help='Add/update/remove this tag, or Add missing tags if empty')
    args = parser.parse_args()

    if args.parent is None:
        raise ValueError("The parent directory must be defined")
    parent = Path(args.parent)
    if not parent.is_dir():
        raise ValueError(f"The parent directory {parent} must exist")

    remove = args.remove or 0
    if args.tag is None and remove != 0:
        raise ValueError(f'Non-zero {remove=} without a specified tag is not allowed')
    
    if args.rebuild_all and (args.tag or remove):
        raise ValueError("--rebuild-all cannot be used with --remove or a specific tag")

    rebuild_tags = list(args.rebuild or [])
    if args.rebuild_from_file:
        listed = Path(args.rebuild_from_file).read_text().split()
        rebuild_tags.extend(t for t in listed if t not in rebuild_tags)
    if rebuild_tags and (args.rebuild_all or args.tag or remove):
        raise ValueError("--rebuild/--rebuild-from-file cannot be combined with "
                         "--rebuild-all, --remove or a positional tag")

    main(parent=parent, push=not args.no_push, remove=remove, tag=args.tag or '',
         rebuild_all=args.rebuild_all, rebuild_tags=rebuild_tags)
    
