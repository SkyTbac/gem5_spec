import os
import sys
from uuid import UUID

from gem5art.artifact import Artifact
from gem5art.run import gem5Run
from gem5art.tasks.tasks import run_job_pool



experiments_repo = Artifact.registerArtifact(
    command = '''
        git clone https://gem5.googlesource.com/public/gem5-resources
        cd gem5-resources
        git checkout 1fe56ffc94005b7fa0ae5634c6edc5e2cb0b7357
        cd src/spec-2017
        git init
        git remote add origin https://github.com/SkyTbac/gem5_spec.git
    ''',
    typ = 'git repo',
    name = 'spec2017 Experiment',
    path =  './',
    cwd = './',
    documentation = '''
        local repo to run spec 2017 experiments with gem5 full system mode;
        resources cloned from https://gem5.googlesource.com/public/gem5-resources upto commit 1fe56ffc94005b7fa0ae5634c6edc5e2cb0b7357 of stable branch
    '''
)

gem5_repo = Artifact.registerArtifact(
    command = '''
        git clone -b v20.1.0.4 https://gem5.googlesource.com/public/gem5
        cd gem5
        scons build/X86/gem5.opt -j8
    ''',
    typ = 'git repo',
    name = 'gem5',
    path =  'gem5/',
    cwd = './',
    documentation = 'cloned gem5 v20.1.0.4'
)


gem5_binary = Artifact.registerArtifact(
    command = 'scons build/X86/gem5.opt -j8',
    typ = 'gem5 binary',
    name = 'gem5-20.1.0.4',
    cwd = 'gem5/',
    path =  'gem5/build/X86/gem5.opt',
    inputs = [gem5_repo,],
    documentation = 'compiled gem5 v20.1.0.4 binary'
)

m5_binary = Artifact.registerArtifact(
    command = 'scons build/x86/out/m5',
    typ = 'binary',
    name = 'm5',
    path =  'gem5/util/m5/build/x86/out/m5',
    cwd = 'gem5/util/m5',
    inputs = [gem5_repo,],
    documentation = 'm5 utility'
)

packer = Artifact.registerArtifact(
    command = '''
        wget https://releases.hashicorp.com/packer/1.6.6/packer_1.6.6_linux_amd64.zip;
        unzip packer_1.6.6_linux_amd64.zip;
    ''',
    typ = 'binary',
    name = 'packer',
    path =  'disk-image/packer',
    cwd = 'disk-image',
    documentation = 'Program to build disk images. Downloaded from https://www.packer.io/.'
)

disk_image = Artifact.registerArtifact(
    command = './packer build spec-2017/spec-2017.json',
    typ = 'disk image',
    name = 'spec-2017',
    cwd = 'disk-image/',
    path = 'disk-image/spec-2017/spec-2017-image/spec-2017',
    inputs = [packer, experiments_repo, m5_binary,],
    documentation = 'Ubuntu Server with SPEC 2017 installed, m5 binary installed and root auto login'
)

linux_binary = Artifact.registerArtifact(
    name = 'vmlinux-4.19.83',
    typ = 'kernel',
    path = './vmlinux-4.19.83',
    cwd = './',
    command = ''' wget http://dist.gem5.org/dist/v21-1/kernels/x86/static/vmlinux-4.19.83''',
    inputs = [experiments_repo,],
    documentation = "kernel binary for v4.19.83",
)

if __name__ == "__main__":
    cpus = ['atomic']
    benchmark_sizes = {'kvm':    ['test', 'ref'],
                       'atomic': ['test'],
                       'o3':     ['test'],
                       'timing': ['test']
                      }
    benchmarks = ["531.deepsjeng_r"]

    runs = []
    for cpu in cpus:
        for size in benchmark_sizes[cpu]:
            for benchmark in benchmarks:
                run = gem5Run.createFSRun(
                    'gem5 v20.1.0.4 spec 2017 experiment', # name
                    'gem5/build/X86/gem5.opt', # gem5_binary
                    'gem5-configs/run_spec.py', # run_script
                    'results/{}/{}/{}'.format(cpu, size, benchmark), # relative_outdir
                    gem5_binary, # gem5_artifact
                    gem5_repo, # gem5_git_artifact
                    run_script_repo, # run_script_git_artifact
                    'linux-4.19.83/vmlinux-4.19.83', # linux_binary
                    'disk-image/spec2017/spec2017-image/spec2017', # disk_image
                    linux_binary, # linux_binary_artifact
                    disk_image, # disk_image_artifact
                    cpu, benchmark, size, # params
                    timeout = 40*60 # 10 days
                )
                runs.append(run)


    run_job_pool(runs)