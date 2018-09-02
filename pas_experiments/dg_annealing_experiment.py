import csv
import time
import os.path
from pas_experiments import get_n
from gambit_analyze_pas import do_gambit_analyze
from create_tsv_files_pas import create_tsv, get_tsv_strat_name
from get_payoff_from_game_pas import get_def_payoff_eq, get_eq_from_file
from enjoy_def_pas import get_def_payoff
from dg_annealing import run_depgraph_annealing
from generate_new_cols_pas import gen_new_cols
from add_new_data_pas import add_data
from depgraph_connect import convert_params_from_0_1, get_def_name
from utility import get_game_file_name, get_result_name, get_deviations_name
from ground_truth_annealing import get_ground_truth_dev_prob

def get_att_eq(run_name, test_round, cur_step):
    att_mixed_strat_name = get_tsv_strat_name(run_name, test_round, cur_step, False)
    if not os.path.isfile(att_mixed_strat_name):
        raise ValueError(att_mixed_strat_name + " missing.")
    att_mixed_strat = get_eq_from_file(att_mixed_strat_name)
    return att_mixed_strat

def convert_deviating_strat_to_def_name(deviating_strat_0_1):
    deviating_strat_java = convert_params_from_0_1(deviating_strat_0_1)
    def_name = get_def_name(deviating_strat_java)
    return def_name

def record_deviations(deviations_name, deviation_sequences):
    with open(deviations_name, 'w') as txt_file:
        for sequence in deviation_sequences:
            txt_file.write(str(sequence) + "\n")

def record_result_tuples(result_name, result_tuples):
    with open(result_name, 'w') as tsv_file:
        csv_writer = csv.writer(tsv_file, delimiter='\t')
        for cur_tuple in result_tuples:
            csv_writer.writerow(cur_tuple)

def get_results(max_p, alpha_list, test_count, max_steps, max_samples, samples_per_param, \
    neighbor_variance, should_print, run_name, samples_new_column, \
    anneal_ground_truth_max, anneal_ground_truth_min, early_stop_level):
    results = []
    deviation_sequences = []
    start_time_all = time.time()
    fmt = "{0:.2f}"
    for test_round in range(test_count):
        start_time_round = time.time()
        cur_step = 0
        was_confirmed = False
        deviation_sequence = []
        while cur_step < max_steps:
            print("new round: test round " + str(test_round) + ", cur step: " + \
                str(cur_step))
            do_gambit_analyze(run_name, test_round, cur_step)
            create_tsv(run_name, test_round, cur_step)

            error_prob_one_side = alpha_list[cur_step]
            cur_n = get_n(max_p, error_prob_one_side)
            if should_print:
                print("cur_n: " + str(cur_n))

            def_payoff_old = get_def_payoff_eq(run_name, test_round, cur_step)
            found_dev = False
            att_mixed_strat = get_att_eq(run_name, test_round, cur_step)
            start_time_sim_annealing = time.time()
            for cur_annealing_step in range(cur_n):
                output_name = get_game_file_name(run_name, test_round, cur_step + 1)
                if os.path.isfile(output_name):
                    print("Skipping, file already exists: " + output_name)
                    break
                # deviating_strat is in [0, 1]^3
                deviating_strat, cur_best_value = run_depgraph_annealing(max_samples, \
                    samples_per_param, neighbor_variance, should_print, None, \
                    att_mixed_strat)
                if should_print:
                    print("Finished annealing round " + str(cur_annealing_step) + " of " + \
                        str(cur_n))
                    print("Mean def payoff to beat was: " + fmt.format(def_payoff_old))
                    print("Estimated best value was: " + fmt.format(cur_best_value))
                def_payoff_cur = get_def_payoff(deviating_strat, run_name, test_round, \
                    cur_step, samples_new_column, att_mixed_strat)
                if def_payoff_cur > def_payoff_old:
                    found_dev = True
                    deviation_sequence.append(deviating_strat)
                    if should_print:
                        print("found deviation after annealing step " + \
                            str(cur_annealing_step) + ", strategy step " + str(cur_step) + \
                            ", round " + str(test_round))
                        print("Best value found: " + fmt.format(cur_best_value))
                        print("Value to beat was: " + fmt.format(def_payoff_old))
                    if cur_step + 1 < max_steps:
                        def_name = convert_deviating_strat_to_def_name(deviating_strat)
                        gen_new_cols(def_name, run_name, test_round, cur_step, \
                            samples_new_column)
                        add_data(run_name, test_round, cur_step)
                    break
                else:
                    if should_print:
                        print("New estimate fails to beat old value: " + \
                            fmt.format(def_payoff_cur))
            seconds_taken_simulated_annealing = time.time() - start_time_sim_annealing
            print("Minutes used for all simulated annealing: " + \
                str(int(seconds_taken_simulated_annealing // 60)))
            if not found_dev:
                if should_print:
                    print("confirmed after step: " + str(cur_step) + ", round " + \
                        str(test_round))
                was_confirmed = True
                break
            cur_step += 1
        ground_truth_dev_prob = get_ground_truth_dev_prob(max_samples, samples_per_param, \
            neighbor_variance, should_print, None, att_mixed_strat, def_payoff_old, \
            anneal_ground_truth_max, anneal_ground_truth_min, early_stop_level)
        cur_result = (was_confirmed, test_round, ground_truth_dev_prob)
        if test_round % 10 == 0:
            print("round " + str(test_round) + " result: " + str(cur_result), flush=True)
        results.append(cur_result)
        deviation_sequences.append(deviation_sequence)
        seconds_taken_round = time.time() - start_time_round
        print("Minutes taken for round " + str(test_round) + " of " + str(test_count) + \
            ": " + str(int(seconds_taken_round // 60)), flush=True)
    seconds_taken_all = time.time() - start_time_all
    print("Minutes taken for all rounds: " + str(int(seconds_taken_all // 60)) + "\n", \
        flush=True)
    return results, deviation_sequences

def main(max_p, error_tolerance, test_count, max_rounds, max_steps, samples_per_param, \
    neighbor_variance, should_print, run_name, samples_new_column, \
    anneal_ground_truth_max, anneal_ground_truth_min, early_stop_level):
    result_name = get_result_name(run_name)
    if os.path.exists(result_name):
        raise ValueError("File exists: " + result_name)
    deviations_name = get_deviations_name(run_name)
    if os.path.exists(deviations_name):
        raise ValueError("File exists: " + deviations_name)

    fmt = "{0:.6f}"
    print("Will run dg_annealing_experiment.py:")
    print("max_p: " + fmt.format(max_p))
    print("error_tolerance: " + fmt.format(error_tolerance))
    print("test_count: " + str(test_count))
    print("max_rounds: " + str(max_rounds))
    print("max_steps: " + str(max_steps))
    print("samples_per_param: " + str(samples_per_param))
    print("neighbor_variance: " + fmt.format(neighbor_variance))
    print("run_name: " + run_name)
    print("samples_new_column: " + str(samples_new_column))
    print("anneal_ground_truth_max: " + str(anneal_ground_truth_max))
    print("anneal_ground_truth_min: " + str(anneal_ground_truth_min))
    print("early_stop_level: " + fmt.format(early_stop_level) + "\n")

    alpha_list = [error_tolerance * 1.0 / max_rounds] * max_rounds
    print("alpha_list: " + str(alpha_list))
    result_tuples, deviation_sequences = get_results(max_p, alpha_list, test_count, \
        max_rounds, max_steps, samples_per_param, neighbor_variance, should_print, \
        run_name, samples_new_column, anneal_ground_truth_max, anneal_ground_truth_min, \
        early_stop_level)
    record_result_tuples(result_name, result_tuples)
    record_deviations(deviations_name, deviation_sequences)

'''
example: python3 dg_annealing_experiment.py
or: stdbuf -i0 -o0 -e0 python3 dg_annealing_experiment.py > out_dg1_b.txt

good debugging values:
(0.2, 0.2, 2, 3, 3, 3, 0.05, True, "dg1", 3, 10, 10, 0.4)

good final values:
(0.05, 0.1, 700, 3, 100, 100, 0.03, True, dg1, 100, 400, 20, 0.1)

compromise final values:
(0.05, 0.1, 1, 3, 20, 50, 0.03, True, dg1_a, 50, 200, 10, 0.1)
'''
if __name__ == "__main__":
    MAX_P = 0.2
    ERROR_TOLERANCE = 0.2
    TEST_COUNT = 2
    MAX_STEPS = 3
    MAX_SAMPLES = 3
    SAMPLES_PER_PARAM = 3
    NEIGHBOR_VARIANCE = 0.05
    SHOULD_PRINT = True
    RUN_NAME = "dg1"
    SAMPLES_NEW_COLUMN = 3
    ANNEAL_GROUND_TRUTH_MAX = 10
    ANNEAL_GROUND_TRUTH_MIN = 10
    EARLY_STOP_LEVEL = MAX_P * 2
    main(MAX_P, ERROR_TOLERANCE, TEST_COUNT, MAX_STEPS, MAX_SAMPLES, SAMPLES_PER_PARAM, \
        NEIGHBOR_VARIANCE, SHOULD_PRINT, RUN_NAME, SAMPLES_NEW_COLUMN, \
        ANNEAL_GROUND_TRUTH_MAX, ANNEAL_GROUND_TRUTH_MIN, EARLY_STOP_LEVEL)