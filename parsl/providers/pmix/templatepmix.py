template_string = '''#!/bin/bash

#SBATCH --job-name=${jobname}
#SBATCH --output=${submit_script_dir}/${jobname}.submit.stdout
#SBATCH --error=${submit_script_dir}/${jobname}.submit.stderr
#SBATCH --nodes=${nodes}
#SBATCH --time=${walltime}
#SBATCH --ntasks-per-node=${tasks_per_node}
${scheduler_options}

${worker_init}

export JOBNAME="${jobname}"

export SCRIPTDIR=${submit_script_dir}

export HOSTFILE=/home/rbhattara/parsl/hostfiles/truncated_hostfile

export HOSTFILE1=/home/rbhattara/parsl/hostfiles/hostfile1

export ADDHOSTFILE=/home/rbhattara/parsl/hostfiles/add_hostfile

export DVMURI=${submit_script_dir}/dvm.uri

env | grep SLURM > ${submit_script_dir}/slurmenv

$user_script
'''
