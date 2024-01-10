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

head -n -${user_nodes} ${submit_script_dir}/hostfile > ${submit_script_dir}/dvm_hostfile
sed -i 's/.*/& slots=64/' "${submit_script_dir}/dvm_hostfile"
tail -${extra_nodes} ${submit_script_dir}/hostfile > ${submit_script_dir}/extra_hostfile
export SCRIPT_DIR=${submit_script_dir}
export DVMURI=${submit_script_dir}/dvm.uri
export WALLTIME=${walltime}

$user_script
'''
