''' Play back the dependency graph network that was learned. '''
import time
import math
import numpy as np
import gym

from baselines import deepq

def main():
    '''
        Load the network from file, and play games of the depdency
        graph game against opponent.

        env_name = "DepgraphJavaAtt-v0"
        model_name = "depgraph_java_deepq_model2.pkl"
    '''

    env_name = "DepgraphJavaAtt-v0"
    model_name = "dg_dqmlp_rand30NoAnd_B_att.pkl"
    num_episodes = 1000

    start_time = time.time()

    env = gym.make(env_name)
    print("Environment: " + env_name)

    act = deepq.load(model_name)
    print("Model: " + model_name)

    rewards = []
    for _ in range(num_episodes):
        obs, done = env.reset(), False
        obs_len = len(obs)
        obs = np.array(obs).reshape(1, obs_len)
        episode_rew = 0
        while not done:
            obs, rew, done, _ = env.step(act(obs)[0])
            obs = np.array(obs).reshape(1, obs_len)
            episode_rew += rew
        rewards.append(episode_rew)
    mean_reward = np.mean(rewards)
    stdev_reward = np.std(rewards)
    stderr_reward = stdev_reward * 1.0 / math.sqrt(num_episodes)

    duration = time.time() - start_time
    fmt = "{0:.2f}"
    print("Mean reward: " + fmt.format(mean_reward))
    print("Stdev reward: " + fmt.format(stdev_reward))
    print("Stderr reward: " + fmt.format(stderr_reward))
    print("Minutes taken: " + str(duration // 60))

if __name__ == '__main__':
    main()
