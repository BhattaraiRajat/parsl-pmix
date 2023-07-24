import os
import math
import time
import re
import logging

from parsl.launchers.base import Launcher
from parsl.providers.base import JobState, JobStatus
from parsl.utils import wtime_to_minutes
from parsl.providers.slurm.slurm import SlurmProvider
from parsl.providers.pmix.templatepmix import template_string

logger = logging.getLogger(__name__)

class PMIxSlurmProvider(SlurmProvider):
    """PMIx Slurm Execution Provider
    """
    def submit(self, command, tasks_per_node, job_name="parsl.slurmpmix"):
        """Submit the command as a slurm job.

        Parameters
        ----------ß
        command : str
            Command to be made on the remote side.
        tasks_per_node : int
            Command invocations to be launched per node
        job_name : str
            Name for the job
        Returns
        -------
        None or str
            If at capacity, returns None; otherwise, a string identifier for the job
        """

        scheduler_options = self.scheduler_options
        worker_init = self.worker_init
        if self.mem_per_node is not None:
            scheduler_options += '#SBATCH --mem={}g\n'.format(self.mem_per_node)
            worker_init += 'export PARSL_MEMORY_GB={}\n'.format(self.mem_per_node) 
        if self.cores_per_node is not None:
            cpus_per_task = math.floor(self.cores_per_node / tasks_per_node)
            scheduler_options += '#SBATCH --cpus-per-task={}'.format(cpus_per_task)
            worker_init += 'export PARSL_CORES={}\n'.format(cpus_per_task)

        # export pmix
        # worker_init += 'export PATH=/users/hpritchard/ompi/install_session_hcoll/bin:$PATH'
        # worker_init += 'source /home/rbhattara/parsl/venv/bin/activate'

        job_name = "{0}.{1}".format(job_name, time.time())

        script_path = "{0}/{1}.submit".format(self.script_dir, job_name)
        script_path = os.path.abspath(script_path)

        logger.debug("Requesting one block with {} nodes".format(self.nodes_per_block))

        job_config = {}
        job_config["submit_script_dir"] = self.channel.script_dir
        job_config["nodes"] = self.nodes_per_block
        job_config["tasks_per_node"] = 256
        job_config["walltime"] = wtime_to_minutes(self.walltime)
        job_config["scheduler_options"] = scheduler_options
        job_config["worker_init"] = worker_init
        job_config["user_script"] = command

        # Wrap the command
        job_config["user_script"] = self.launcher(command,
                                                  tasks_per_node,
                                                  self.nodes_per_block)

        logger.debug("Writing submit script")
        self._write_submit_script(template_string, script_path, job_name, job_config)

        if self.move_files:
            logger.debug("moving files")
            channel_script_path = self.channel.push_file(script_path, self.channel.script_dir)
        else:
            logger.debug("not moving files")
            channel_script_path = script_path

        retcode, stdout, stderr = self.execute_wait("sbatch {0}".format(channel_script_path))

        job_id = None
        if retcode == 0:
            for line in stdout.split('\n'):
                match = re.match(self.regex_job_id, line)
                if match:
                    job_id = match.group("id")
                    self.resources[job_id] = {'job_id': job_id, 'status': JobStatus(JobState.PENDING)}
                    break
            else:
                logger.error("Could not read job ID from sumbit command standard output.")
                logger.error("Retcode:%s STDOUT:%s STDERR:%s", retcode, stdout.strip(), stderr.strip())
        else:
            logger.error("Submit command failed")
            logger.error("Retcode:%s STDOUT:%s STDERR:%s", retcode, stdout.strip(), stderr.strip())

        return job_id
