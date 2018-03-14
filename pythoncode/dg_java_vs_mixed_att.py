'''
Dependency graph game.

Requirements:
    Py4J        https://www.py4j.org/download.html
    OpenAI Gym  https://github.com/openai/gym#installation
'''

import csv
import random
from py4j.java_gateway import JavaGateway
import numpy as np
import gym
from gym import spaces

NODE_COUNT = 30
AND_NODE_COUNT = 5
EDGE_TO_OR_NODE_COUNT = 100

DEF_OBS_LENGTH = 3
ATT_OBS_LENGTH = 1

DEF_ACTION_COUNT = NODE_COUNT + 1
ATT_ACTION_COUNT = AND_NODE_COUNT + EDGE_TO_OR_NODE_COUNT + 1

DEF_INPUT_DEPTH = 2 + DEF_OBS_LENGTH * 2

DEF_OBS_SIZE = NODE_COUNT * DEF_INPUT_DEPTH
ATT_OBS_SIZE = (AND_NODE_COUNT + EDGE_TO_OR_NODE_COUNT) * 2 + NODE_COUNT * ATT_OBS_LENGTH + 1

ATT_MIXED_STRAT_FILE = "randNoAnd_B_epoch2_att.tsv"
ATT_STRAT_TO_PROB = {}
IS_HEURISTIC_ATTACKER = False

JAVA_GAME = None
GATEWAY = None
IS_DEF_TURN = None

class DepgraphJavaEnvVsMixedAtt(gym.Env):
    """
    Depgraph game environment. Play against a fixed opponent.
    """
    metadata = {"render.modes": ["human"]}

    def __init__(self):
        # https://www.py4j.org/getting_started.html
        global GATEWAY
        GATEWAY = JavaGateway()
        global JAVA_GAME
        JAVA_GAME = GATEWAY.entry_point.getGame()

        self.setup_att_mixed_strat(ATT_MIXED_STRAT_FILE)

        # One action for each node or pass
        # action space is {0, . . ., NODE_COUNT}, indicating node or pass.
        self.action_space = spaces.Discrete(NODE_COUNT + 1)

        observation = self.reset()
        # convert from JavaMember object to JavaList
        observation = observation[:]
        my_shape = (len(observation),)
        self.observation_space = \
            spaces.Box(np.zeros(my_shape), np.ones(my_shape))

    def _reset(self):
        global IS_DEF_TURN
        global IS_HEURISTIC_ATTACKER

        IS_DEF_TURN = True

        cur_att_strat = self.sample_mixed_strat()
        IS_HEURISTIC_ATTACKER = DepgraphJavaEnvVsMixedAtt.is_heuristic_strategy(cur_att_strat)
        is_heuristic_str = "" + IS_HEURISTIC_ATTACKER

        result_values = JAVA_GAME.reset([is_heuristic_str, cur_att_strat])
        # result_values is a Py4J JavaList -> should convert to Python list
        if IS_HEURISTIC_ATTACKER:
            return np.array([x for x in result_values])

        def_obs = result_values[:DEF_OBS_SIZE]
        def_obs = np.array([x for x in def_obs])
        def_obs = def_obs.reshape(1, def_obs.size)
        return def_obs

    def _step(self, action):
        if IS_HEURISTIC_ATTACKER:
            return self._step_vs_heuristic(action)
        return self._step_vs_network(action)

    def _step_vs_heuristic(self, action):
        # action is a numpy.int64, need to convert to Python int before using with Py4J
        action_scalar = np.asscalar(action)
        # {1, . . ., NODE_COUNT} are node ids, (NODE_COUNT + 1) means "pass"
        action_id = action_scalar + 1
        return DepgraphJavaEnvVsMixedAtt.step_result_from_list_heuristic( \
            JAVA_GAME.step(action_id))

    def _step_vs_network(self, action):
        global IS_DEF_TURN

        if not IS_DEF_TURN:
            raise ValueError("Must be defender's turn here.")

        # action is a numpy.int64, need to convert to Python int before using with Py4J
        action_scalar = np.asscalar(action)
        action_id = action_scalar + 1

        both_obs, is_done, state_dict, is_def_turn_local = \
            DepgraphJavaEnvVsMixedAtt.step_result_from_list_network( \
                JAVA_GAME.step(action_id))

        IS_DEF_TURN = is_def_turn_local

        def_obs = both_obs[:DEF_OBS_SIZE]
        att_obs = both_obs[DEF_OBS_SIZE:]

        cur_obs = def_obs
        if not IS_DEF_TURN:
            # FIXME: run attacker network until it makes its move, then return result
            cur_obs = att_obs
        cur_obs = np.array([x for x in cur_obs])
        cur_obs = cur_obs.reshape(1, cur_obs.size)

        def_reward = JAVA_GAME.getSelfMarginalPayoff()
        return cur_obs, def_reward, is_done, state_dict

    @staticmethod
    def is_heuristic_strategy(strategy):
        return ".pkl" not in strategy

    @staticmethod
    def step_result_from_list_heuristic(a_list):
        '''
        Convert a flat list input, a_list, to the observation, reward,
        is_done, and state dictionary.
        a_list will be a list of floats, of length (NODE_COUNT * DEF_INPUT_DEPTH+ 2).

        The first (NODE_COUNT * DEF_INPUT_DEPTH) elements of a_list represent the game state.

        The next element represents the reward, in R-.

        The last element represents whether the game is done, in {0.0, 1.0}.
        '''
        game_size = NODE_COUNT * DEF_INPUT_DEPTH

        obs_values = a_list[:game_size]
        # obs_values is a Py4J JavaList -> should convert to Python list
        obs = np.array([x for x in obs_values])

        reward = a_list[game_size]

        tolerance = 0.01
        is_done = abs(a_list[game_size + 1] - 1) < tolerance

        state_dict = {'state': obs[:]}
        return obs, reward, is_done, state_dict

    @staticmethod
    def step_result_from_list_network(a_list):
        '''
        Convert a flat list input, a_list, to the observation (for defender, then
        attacker), reward, is_done, state dictionary, and is_def_turn_local.

        The first game_size elements of a_list represent the game state, first for the
        defender's view, then the attacker's.

        The next element represents the reward, in R.

        The next element represents whether the game is done, in {0.0, 1.0}.

        The last element represents whether it is the defender's turn, in {0.0, 1.0}.
        '''
        game_size = DEF_OBS_SIZE + ATT_OBS_SIZE

        both_obs = a_list[:game_size]
        # both_obs is a Py4J JavaList -> should convert to Python list
        both_obs = np.array([x for x in both_obs])

        # edit DepgraphPy4JDefVsNetOrHeuristic to return this.
        tolerance = 0.01
        is_done = abs(a_list[game_size] - 1) < tolerance

        state_dict = {'state': both_obs[:]}

        is_def_turn_local = abs(a_list[game_size + 1] - 1) < tolerance
        return both_obs, is_done, state_dict, is_def_turn_local

    def setup_att_mixed_strat(self, strat_file):
        global ATT_STRAT_TO_PROB
        ATT_STRAT_TO_PROB = {}
        with open(strat_file, 'r') as tsv_in:
            row = csv.reader(tsv_in, delimiter='\t')
            if row:
                strat = row[0]
                prob = float(row[1])
                if prob < 0.0 or prob > 1.0:
                    raise ValueError("Invalid prob: " + str(prob))
                if strat in ATT_STRAT_TO_PROB:
                    raise ValueError("Duplicate strat: " + strat)
                ATT_STRAT_TO_PROB[strat] = prob
        tol = 0.001
        if abs(sum(ATT_STRAT_TO_PROB.values()) - 1.0) > tol:
            raise ValueError("Wrong sum of probabilities: " + \
                str(sum(ATT_STRAT_TO_PROB.values())))

    def sample_mixed_strat(self):
        rand_draw = random.random()
        total_prob = 0.0
        for strat, prob in ATT_STRAT_TO_PROB.items():
            total_prob += prob
            if rand_draw <= total_prob:
                return strat
        # should not get here
        return ATT_STRAT_TO_PROB.keys()[0]

    def _render(self, mode='human', close=False):
        if close:
            return
        print(JAVA_GAME.render())

    def get_opponent_reward(self):
        '''
        Get the total discounted reward of the opponent (attacker) in the current game.
        '''
        return JAVA_GAME.getOpponentTotalPayoff()

    def get_self_reward(self):
        '''
        Get the total discounted reward of self (defender) in the current game.
        '''
        return JAVA_GAME.getSelfTotalPayoff()