import time
from statsmodels.stats.proportion import proportion_confint
from dg_annealing import run_depgraph_annealing

def should_continue_anneal(count_so_far, beneficial_count, \
    anneal_ground_truth_max, anneal_ground_truth_min, early_stop_level):
    if count_so_far < anneal_ground_truth_min:
        return True
    if count_so_far >= anneal_ground_truth_max:
        return False
    if beneficial_count * 1. / count_so_far <= early_stop_level:
        return True
    clopper_pearson_min = proportion_confint(beneficial_count, count_so_far, alpha=0.1, \
        method='beta')[0]
    return clopper_pearson_min <= early_stop_level

def get_ground_truth_dev_prob(max_steps, samples_per_param, neighbor_variance, \
                              should_print, initial_params, att_mixed_strat, \
                              def_payoff_old, anneal_ground_truth_max, \
                              anneal_ground_truth_min, early_stop_level):
    if anneal_ground_truth_max < anneal_ground_truth_min or \
        anneal_ground_truth_min < 1 or early_stop_level <= 0.0 or early_stop_level > 1.0:
        raise ValueError("invalid inputs")
    start_time = time.time()
    print("Will run simulated annealing, up to " + str(anneal_ground_truth_max) + \
        " times.")
    print_freq = 25
    beneficial_count = 0
    count_so_far = 0
    while should_continue_anneal(count_so_far, beneficial_count, anneal_ground_truth_max, \
            anneal_ground_truth_min, early_stop_level):
        _, cur_value = run_depgraph_annealing(max_steps, samples_per_param, \
            neighbor_variance, should_print, initial_params, att_mixed_strat)
        count_so_far += 1
        if cur_value > def_payoff_old:
            beneficial_count += 1
        if (count_so_far) % print_freq == 0:
            print("Finished round: " + str(count_so_far))
    duration = time.time() - start_time
    print("Minutes taken for getting ground truth dev prob: " + str(int(duration // 60)))
    print("Rounds used simulated annealing: " + str(count_so_far) + ", of possible " + \
        str(anneal_ground_truth_max))
    return beneficial_count * 1. / count_so_far