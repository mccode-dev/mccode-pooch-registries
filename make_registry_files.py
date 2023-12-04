def make_registry(dirs, output, recursive=True):
    from pathlib import Path
    from pooch import file_hash
    pattern = '**/*' if recursive else '*'
    hashes = {p.as_posix(): file_hash(p) for d in dirs for p in Path(d).glob(pattern) if p.is_file()}
    names = sorted(hashes.keys())
    with open(output, 'w') as outfile:
        for name in names:
            outfile.write(f'{name} {hashes[name]}\n')



if __name__ == '__main__':
    registries = {
        'mcstas': ('mcstas-comps',),
        'mcxtrace': ('mcxtrace-comps',),
        'libc': ('common/lib/share', 'mcstas/nlib', 'mxctrace/xlib'),
    }
    for name, dirs in registries.items():
        make_registry(dirs, f'{name}-registry.txt')

