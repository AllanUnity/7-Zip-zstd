import hashlib
import shutil
import subprocess
import os
import os.path
import sys


if len(sys.argv) != 2:
    raise SystemExit('expected exactly one argument: version_string (will be trimmed to 12 chars)')

version_string = sys.argv[1][:12]
seven_zip = 'CPP/7zip/Bundles/Alone/AMD64/7za.exe'
seven_zip_x86 = 'CPP/7zip/Bundles/Alone/IA32/7za.exe'

source_artifact = 'stevedore-source/7za-source-7zip.7z'

if not os.path.exists(seven_zip):
    raise SystemExit('7za not found at path: ' + seven_zip)

for p in 'stevedore-source', 'stevedore-binary':
    if not os.path.isdir(p):
        os.makedirs(p)

files = subprocess.check_output(['git', 'ls-files'], universal_newlines=True)
with open('filelist-tmp', 'w') as f:
    f.write(files)

if os.path.exists(source_artifact): os.unlink(source_artifact)
subprocess.check_call([seven_zip, '-m0=lzma', '-mx=9', 'a', '-i@filelist-tmp', source_artifact])

with open(source_artifact, 'rb') as f:
    artifact_hash = hashlib.sha256(f.read()).hexdigest()

name, ext = os.path.splitext(os.path.basename(source_artifact))
source_artifact_id = name + '/' + version_string + '_' + artifact_hash + ext
print('Source artifact: ' + source_artifact_id)

def generate_binary_license_file():
    with open('LICENSE.md', 'r') as f:
        first, remaining = f.read().split('\n##', 1)

    return ''.join([
        # Print first section (up until '##'), without trailing blank lines.
        first.rstrip(),

        # Print extra section about source availability.
        '''

The complete corresponding source code should be available from the same
server from which you downloaded this binary, with this artifact ID:

    {0}

If the server was the public Unity-Technologies Stevedore repository:
https://public-stevedore.unity3d.com/r/public/{0}

You may find cloning the Git repository more convenient:
https://github.com/Unity-Technologies/7-Zip-zstd
https://github.com/Unity-Technologies/p7zip-zstd


##'''.format(source_artifact_id),
        # Print remaining LICENSE.md sections.
        remaining,
    ])

for binary_path, artifact_tag in [
    (seven_zip, 'win-x64'),
    (seven_zip_x86, 'win-x86'),
]:
    # Must use .zip format for the binary artifact, of course.
    artifact_filename = 'stevedore-binary/7za-%s.zip' % artifact_tag
    if os.path.exists(artifact_filename): os.unlink(artifact_filename)

    tmp = 'build-artifact-tmp'
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.mkdir(tmp)

    shutil.copy('GPL-2.0.txt', tmp)
    shutil.copy(binary_path, tmp + '/7za.exe')
    with open(tmp + '/LICENSE.md', 'w') as f:
        f.write(generate_binary_license_file())

    subprocess.check_call([seven_zip, 'a', '../' + artifact_filename], cwd=tmp)
