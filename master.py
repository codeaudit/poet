# Copyright (c) 2019 Uber Technologies, Inc.
#
# Licensed under the Uber Non-Commercial License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at the root directory of this project.
#
# See the License for the specific language governing permissions and
# limitations under the License.


from argparse import ArgumentParser
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import numpy as np

from poet_distributed.es import initialize_worker  # noqa
from poet_distributed.poet_algo import MultiESOptimizer  # noqa

parser = ArgumentParser()
parser.add_argument('log_file')
parser.add_argument('--init', default='random')
parser.add_argument('--learning_rate', type=float, default=0.01)
parser.add_argument('--lr_decay', type=float, default=0.9999)
parser.add_argument('--lr_limit', type=float, default=0.001)
parser.add_argument('--noise_std', type=float, default=0.1)
parser.add_argument('--noise_decay', type=float, default=0.999)
parser.add_argument('--noise_limit', type=float, default=0.01)
parser.add_argument('--l2_coeff', type=float, default=0.01)
parser.add_argument('--batches_per_chunk', type=int, default=50)
parser.add_argument('--batch_size', type=int, default=64)
parser.add_argument('--eval_batch_size', type=int, default=1)
parser.add_argument('--eval_batches_per_step', type=int, default=50)
parser.add_argument('--n_iterations', type=int, default=200)
parser.add_argument('--steps_before_transfer', type=int, default=25)
parser.add_argument('--master_seed', type=int, default=111)
parser.add_argument('--repro_threshold', type=int, default=100)
parser.add_argument('--mc_lower', type=int, default=25)
parser.add_argument('--mc_upper', type=int, default=340)
parser.add_argument('--max_num_envs', type=int, default=100)
parser.add_argument('--adjust_interval', type=int, default=6)
parser.add_argument('--normalize_grads_by_noise_std', action='store_true', default=False)
parser.add_argument('--propose_with_adam', action='store_true', default=False)
parser.add_argument('--checkpointing', action='store_true', default=False)
parser.add_argument('--returns_normalization', default='normal')
parser.add_argument('--stochastic', action='store_true', default=False)
parser.add_argument('--envs', nargs='+')
parser.add_argument('--start_from', default=None)  # Json file to start from

args = parser.parse_args()
logger.info(args)

def run_main(args):
    import ipyparallel as ipp

    client = ipp.Client()
    engines = client[:]
    engines.block = True
    scheduler = client.load_balanced_view()
    engines.apply(initialize_worker)

    #set master_seed
    np.random.seed(args.master_seed)

    optimizer_zoo = MultiESOptimizer(args=args, engines=engines, scheduler=scheduler,
                                     client=client)

    optimizer_zoo.optimize(iterations=args.n_iterations,
                       propose_with_adam=args.propose_with_adam,
                       reset_optimizer=True,
                       checkpointing=args.checkpointing,
                       steps_before_transfer=args.steps_before_transfer)
    #client.shutdown()

run_main(args)
