import os
import math
import time
import re
import logging

import typeguard

from typing import Optional

from parsl.launchers.base import Launcher
from parsl.providers.base import JobState, JobStatus
from parsl.utils import wtime_to_minutes
from parsl.providers.slurm.slurm import SlurmProvider
from parsl.providers.pmix.templatepmix import template_string
from parsl.providers.pmix.templateelasticpmix import template_elastic_string

from parsl.channels import LocalChannel
from parsl.channels.base import Channel
from parsl.launchers import SingleNodeLauncher

logger = logging.getLogger(__name__)

class PMIxSlurmProvider(SlurmProvider):
    """PMIx Slurm Execution Provider
    """
    @typeguard.typechecked
    def __init__(self,
                 partition: Optional[str] = None,
                 account: Optional[str] = None,
                 channel: Channel = LocalChannel(),
                 nodes_per_block: int = 1,
                 cores_per_node: Optional[int] = None,
                 mem_per_node: Optional[int] = None,
                 expand_at: Optional[int] = None,
                 expand_by: Optional[int] = None,
                 init_blocks: int = 1,
                 min_blocks: int = 0,
                 max_blocks: int = 1,
                 parallelism: float = 1,
                 walltime: str = "00:10:00",
                 scheduler_options: str = '',
                 regex_job_id: str = r"Submitted batch job (?P<id>\S*)",
                 worker_init: str = '',
                 cmd_timeout: int = 10,
                 exclusive: bool = True,
                 move_files: bool = True,
                 launcher: Launcher = SingleNodeLauncher(),):
        
        super().__init__(
                 partition,
                 account,
                 channel,
                 nodes_per_block,
                 cores_per_node,
                 mem_per_node,
                 init_blocks,
                 min_blocks,
                 max_blocks,
                 parallelism,
                 walltime,
                 scheduler_options,
                 regex_job_id,
                 worker_init,
                 cmd_timeout,
                 exclusive,
                 move_files,
                 launcher)
        
        self.expand_at = expand_at
        self.expand_by = expand_by
        
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

        worker_init += 'export OMPI_MCA_pml=^ucx'
        worker_init += 'export PRTE_MCA_ras=simulator'

        job_name = "{0}.{1}".format(job_name, time.time())

        script_path = "{0}/{1}.submit".format(self.script_dir, job_name)
        script_path = os.path.abspath(script_path)

        worker_init += 'export USER_NODE_COUNT={}\n'.format(self.nodes_per_block)

        if(self.expand_at is not None):
            worker_init += 'export EXPAND_AT={}\n'.format(self.expand_at)
            worker_init += 'export EXPAND_BY={}\n'.format(self.expand_by)
            # ask for more nodes for DVM expansion
            self.nodes_per_block = self.nodes_per_block + self.expand_by


        logger.debug("Requesting one block with {} nodes".format(self.nodes_per_block))

        job_config = {}
        job_config["submit_script_dir"] = self.channel.script_dir
        job_config["nodes"] = self.nodes_per_block
        job_config["tasks_per_node"] = 256
        job_config["walltime"] = wtime_to_minutes(self.walltime)
        job_config["scheduler_options"] = scheduler_options
        job_config["worker_init"] = worker_init
        job_config["user_script"] = command

        if(self.expand_at is not None):
            job_config["expand_by"] = self.expand_by

        # Wrap the command
        job_config["user_script"] = self.launcher(command,
                                                  tasks_per_node,
                                                  self.nodes_per_block)

        logger.debug("Writing submit script")
        if self.expand_at is not None:
            self._write_submit_script(template_elastic_string, script_path, job_name, job_config)
        else:
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
