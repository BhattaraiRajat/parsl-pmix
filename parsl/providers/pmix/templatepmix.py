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

tail -1 ${submit_script_dir}/hostfile > ${submit_script_dir}/add_hostfile

export ADDHOSTFILE=${submit_script_dir}/add_hostfile

head -n -1 ${submit_script_dir}/hostfile > ${submit_script_dir}/truncated_hostfile

export TRUNCATED_HOSTFILE=${submit_script_dir}/truncated_hostfile

export DVMURI=${submit_script_dir}/dvm.uri

env | grep SLURM > ${submit_script_dir}/slurmenv

$user_script
'''
