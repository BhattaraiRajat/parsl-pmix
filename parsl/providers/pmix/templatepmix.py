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

scontrol show hostnames > ${submit_script_dir}/hostfile

head -n -1 ${submit_script_dir}/hostfile > ${submit_script_dir}/truncated_hostfile

export SCRIPT_DIR=${submit_script_dir}

export TRUNCATED_HOSTFILE=${submit_script_dir}/truncated_hostfile

export DVMURI=${submit_script_dir}/dvm.uri

split --numeric-suffixes -l 1 ${submit_script_dir}/hostfile ${submit_script_dir}/hostfile

env | grep SLURM > ${submit_script_dir}/slurmenv

$user_script
'''
