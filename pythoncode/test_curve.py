'''
Run a trained network and save_count retrained versions, for
attacker or defender, playing each such network for runs_per_pair runs against each of
the current equilibrium strategy and against the modified (weighted mean) mixed
strategy. Record the results to a Json file.
'''
import sys
import json
import subprocess
import time
from os import chdir
import os.path

def get_truth_value(str_input):
    '''
    Return True or False after string conversion, else throw error.
    '''
    if str_input == "True":
        return True
    if str_input == "False":
        return False
    raise ValueError("Must be True or False: " + str_input)

def get_cur_tsv_name(env_short_name_payoffs, is_defender_net):
    '''
    Look in the config file for defender or attacker, which should have one line, with
    a double-quoted string in it. Get that inner string, and return it. This is the TSV
    file the config file pointed to.
    '''
    gym_folder = "gym/gym/gym/envs/board_game/"
    config_name = gym_folder + env_short_name_payoffs
    if is_defender_net:
        config_name += "_att" # network defender is self, opponent is att
    else:
        config_name += "_def"
    config_name += "_config.py"

    lines = get_file_lines(config_name)
    if len(lines) != 1:
        raise ValueError("Invalid lines in config: " + str(lines))
    return get_string_from_line(lines[0])

def get_modified_tsv_name(env_short_name_tsv, cur_epoch, is_defender_net, \
    old_strat_disc_fact):
    '''
    Generate the name of the TSV file that would be created for the given environment,
    epoch, attacker/defender option, as discount factor when mixing old strategies.
    '''
    type_string = "_def.tsv"
    if not is_defender_net:
        type_string = "_att.tsv"
    fmt = "{0:.2f}"
    return env_short_name_tsv + "_epoch" + str(cur_epoch) + "_mixed" + \
        fmt.format(old_strat_disc_fact).replace('.', '_') + type_string

def set_config_name(env_short_name_payoffs, modified_tsv_name, is_defender_net):
    '''
    Update the TSV file pointed to by the config file for attacker or defender, to point
    to modified_tsv_name.
    '''
    gym_folder = "gym/gym/gym/envs/board_game/"
    if is_defender_net:
        # network defender is self, opponent is att
        config_file_name_att = gym_folder + env_short_name_payoffs + "_att_config.py"
        write_line(config_file_name_att, "ATT_MIXED_STRAT_FILE = \"" + \
            modified_tsv_name + "\"")
    else:
        config_file_name_def = gym_folder + env_short_name_payoffs + "_def_config.py"
        write_line(config_file_name_def, "DEF_MIXED_STRAT_FILE = \"" + \
            modified_tsv_name + "\"")

def start_and_return_env_process(graph_name, is_defender_net):
    '''
    Start a process running the Java server for the attacker or defender environment, with
    the given graph.
    '''
    cmd = "exec java -jar ../depgraphpy4jattvseither/" \
        + "depgraphpy4jattvsnetorheuristic.jar " \
        + graph_name

    if is_defender_net:
        cmd = "exec java -jar ../depgraphpy4jdefvseither/" \
            + "depgraphpy4jdefvsnetorheuristic.jar " \
            + graph_name
    env_process = subprocess.Popen(cmd, shell=True)
    sleep_sec = 5
    # wait for Java server to start
    time.sleep(sleep_sec)
    return env_process

def close_env_process(env_process):
    '''
    Wait as a precaution, then kill the given process.
    '''
    sleep_sec = 5
    time.sleep(sleep_sec)
    env_process.kill()

def get_pickle_names(env_short_name_payoffs, cur_epoch, is_defender_net, save_count):
    '''
    Return a list of the names of the pickle network files, for the given environment,
    epoch, attacker/defender choice, and number of saves generated during retraining.
    Will include the original network and save_count retrained versions, in the order they
    would be generated.
    '''
    result = []
    for i in range(save_count + 1):
        cur = "dg_" + env_short_name_payoffs + "_dq_mlp_rand_epoch" + str(cur_epoch)
        if not is_defender_net:
            cur += "_att"
        if i > 0:
            cur += "_afterRetrain_r" + str(i)
        cur += ".pkl"
        result.append(cur)
    return result

def get_net_scopes(is_defender_net, cur_epoch, save_count):
    '''
    Return a list of the scope of each pickle network file, for the given attacker/defender
    choice, epoch, and save_count of retrained files. Will be in the same order as the
    result of get_pickle_names().
    '''
    result = []
    for i in range(save_count + 1):
        cur = "deepq_train_e" + str(cur_epoch)
        if not is_defender_net:
            cur += "_att"
        if i > 0:
            cur += "_retrained"
        result.append(cur)
    return result

def run_evaluation_def_net(env_name_vs_mixed_att, model_name, scope, save_name, \
    runs_per_pair):
    '''
    Plays back (enjoys) model_name defender network against the given environment, saving
    the output as save_name, with runs_per_pair games played.
    '''
    cmd_list = ["python3", "enjoy_depgraph_data_vs_mixed_mod_net.py", \
        env_name_vs_mixed_att, model_name, scope, runs_per_pair]
    if os.path.isfile(save_name):
        print("Skipping: " + save_name + " already exists.")
        return
    with open(save_name, "w") as file:
        subprocess.call(cmd_list, stdout=file)

def run_evaluation_att_net(env_name_vs_mixed_def, model_name, scope, save_name, \
    runs_per_pair):
    '''
    Plays back (enjoys) model_name attacker network against the given environment, saving
    the output as save_name, with runs_per_pair games played.
    '''
    cmd_list = ["python3", "enjoy_dg_data_vs_mixed_def_mod_net.py", \
        env_name_vs_mixed_def, model_name, scope, runs_per_pair]
    if os.path.isfile(save_name):
        print("Skipping: " + save_name + " already exists.")
        return
    with open(save_name, "w") as file:
        subprocess.call(cmd_list, stdout=file)

def get_mean_stdev(file_name):
    '''
    Read the lines from the given file.
    The first line will be like "Mean reward: ?",
    the second line like "Stdev reward: ?", where "?" is some real value.
    Return a tuple (mean, stdev).
    '''
    lines = get_file_lines(file_name)
    mean_line = lines[0]
    stdev_line = lines[1]
    mean_line = mean_line[mean_line.find(":") + 1 : ].strip() # get value after colon
    stdev_line = stdev_line[stdev_line.find(":") + 1 : ].strip()
    mean = float(mean_line)
    stdev = float(stdev_line)
    return (mean, stdev)

def write_line(file_name, line):
    '''
    Overwrite the given file with the given line.
    '''
    with open(file_name, "w") as file:
        file.write(line)

def print_json(file_name, json_obj):
    '''
    Prints the given Json object to the given file name.
    '''
    with open(file_name, 'w') as my_file:
        json.dump(json_obj, my_file)

def get_file_lines(file_name):
    '''
    Return the file's text as a list of strings.
    '''
    lines = []
    with open(file_name) as file:
        lines = file.readlines()
    lines = [x.strip() for x in lines]
    lines = [x for x in lines if x] # remove empty lines
    return lines

def get_string_from_line(line):
    '''
    Take a string of text called "line", which should have a double-quoted string in it,
    and return the contents of that double-quoted part.
    '''
    first_double_quote = line.index("\"")
    second_double_quote = line.index("\"", first_double_quote + 1)
    return line[first_double_quote + 1 : second_double_quote]

def main(env_short_name_tsv, env_short_name_payoffs, cur_epoch, old_strat_disc_fact, \
         save_count, graph_name, is_defender_net, runs_per_pair,
         env_name_vs_mixed_def, env_name_vs_mixed_att):
    '''
    Iterate over the original trained network and save_count retrained versions, for
    attacker or defender, playing each such network for runs_per_pair runs against each of
    the current equilibrium strategy and against the modified (weighted mean) mixed
    strategy. Record the results to a Json file.
    '''
    if cur_epoch < 1:
        # can't call this in epoch 0, because no weighted mean strategy exists yet.
        raise ValueError("cur_epoch must be >= 1: " + str(cur_epoch))
    if old_strat_disc_fact <= 0.0 or old_strat_disc_fact > 1.0:
        raise ValueError("old_strat_disc_fact must be in (0, 1]: " + \
            str(old_strat_disc_fact))
    if save_count < 1:
        raise ValueError("save_count must be >= 1: " + str(save_count))
    if runs_per_pair < 2:
        raise ValueError("runs_per_pair must be >= 2: " + str(runs_per_pair))

    # pwd is ~/
    result_file_name = "curve_" + env_short_name_payoffs + "_e" + str(cur_epoch)
    if is_defender_net:
        result_file_name += "_def.json"
    else:
        result_file_name += "_att.json"
    if os.path.isfile(result_file_name):
        raise ValueError("Skipping: " + result_file_name + " already exists.")

    # get name of current TSV file pointed to by environment, for resetting after run.
    old_tsv_name = get_cur_tsv_name(env_short_name_payoffs, is_defender_net)
    # derive the name of the new modified (weighted mean) opponent strategy.
    modified_tsv_name = get_modified_tsv_name(env_short_name_tsv, cur_epoch, \
        is_defender_net, old_strat_disc_fact)
    if not os.path.isfile("pythoncode/" + old_tsv_name):
        raise ValueError("Skipping: " + old_tsv_name + " does not exist.")
    if not os.path.isfile("pythoncode/" + modified_tsv_name):
        raise ValueError("Skipping: " + modified_tsv_name + " does not exist.")

    # derive names and corresponding scopes of trained, retrained models to evaluate.
    model_names = get_pickle_names(env_short_name_payoffs, cur_epoch, is_defender_net, \
        save_count)
    scopes = get_net_scopes(is_defender_net, cur_epoch, save_count)
    for model_name in model_names:
        if not os.path.isfile("pythoncode/" + model_name):
            raise ValueError("Skipping: " + model_name + " does not exist.")

    print("old_tsv_name: " + old_tsv_name)
    # update config file to point to modified (weighted mean) opponent strategy
    set_config_name(env_short_name_payoffs, modified_tsv_name, is_defender_net)
    if get_cur_tsv_name(env_short_name_payoffs, is_defender_net) != modified_tsv_name:
        raise ValueError("Failed to set config name: " + str(modified_tsv_name))

    # construct result object for saving as Json
    result = {}
    result["original_opponent_strat"] = old_tsv_name
    result["modified_opponent_strat"] = modified_tsv_name
    result["runs_per_pair"] = runs_per_pair
    result["outcomes"] = {}

    chdir("pythoncode")
    # pwd is ~/pythoncode
    # start server to run opponent with modified strategy
    env_process = start_and_return_env_process(graph_name, is_defender_net)

    for i in range(len(model_names)):
        model_name = model_names[i]
        scope = scopes[i]
        result["outcomes"][model_name] = {}
        if is_defender_net:
            save_name = "def_" + env_short_name_payoffs + "_epoch" + str(cur_epoch) + \
                "_r" + str(i) + "_mod_enj.txt"
            # run model_name against modified opponent attacker
            run_evaluation_def_net(env_name_vs_mixed_att, model_name, scope, save_name, \
                runs_per_pair)
            (mean, stdev) = get_mean_stdev(save_name)
            print(model_name + " vs. " + modified_tsv_name)
            print(str(mean) + "\t" + str(stdev))
            result["outcomes"][model_name]["vs_modified_mean"] = mean
            result["outcomes"][model_name]["vs_modified_stdev"] = stdev
        else:
            save_name = "att_" + env_short_name_payoffs + "_epoch" + str(cur_epoch) + \
                "_r" + str(i) + "_mod_enj.txt"
            # run model_name against modified opponent defender
            run_evaluation_att_net(env_name_vs_mixed_def, model_name, scope, save_name, \
                runs_per_pair)
            (mean, stdev) = get_mean_stdev(save_name)
            print(model_name + " vs. " + modified_tsv_name)
            print(str(mean) + "\t" + str(stdev))
            result["outcomes"][model_name]["vs_modified_mean"] = mean
            result["outcomes"][model_name]["vs_modified_stdev"] = stdev

    # shut down opponent server that used modified opponent strategy
    close_env_process(env_process)
    # reset config to use original opponent strategy
    set_config_name(env_short_name_payoffs, old_tsv_name, is_defender_net)
    if get_cur_tsv_name(env_short_name_payoffs, is_defender_net) != old_tsv_name:
        raise ValueError("Failed to reset config name: " + str(old_tsv_name))
    # start opponent server using original opponent strategy
    env_process = start_and_return_env_process(graph_name, is_defender_net)

    for i in range(len(model_names)):
        model_name = model_names[i]
        scope = scopes[i]
        if is_defender_net:
            save_name = "def_" + env_short_name_payoffs + "_epoch" + str(cur_epoch) + \
                "_r" + str(i) + "_enj.txt"
            # run model_name against original opponent attacker
            run_evaluation_def_net(env_name_vs_mixed_att, model_name, scope, save_name, \
                runs_per_pair)
            (mean, stdev) = get_mean_stdev(save_name)
            print(model_name + " vs. " + old_tsv_name)
            print(str(mean) + "\t" + str(stdev))
            result["outcomes"][model_name]["vs_original_mean"] = mean
            result["outcomes"][model_name]["vs_original_stdev"] = stdev
        else:
            save_name = "att_" + env_short_name_payoffs + "_epoch" + str(cur_epoch) + \
                "_r" + str(i) + "_enj.txt"
            # run model_name against original opponent defender
            run_evaluation_att_net(env_name_vs_mixed_def, model_name, scope, save_name, \
                runs_per_pair)
            (mean, stdev) = get_mean_stdev(save_name)
            print(model_name + " vs. " + old_tsv_name)
            print(str(mean) + "\t" + str(stdev))
            result["outcomes"][model_name]["vs_original_mean"] = mean
            result["outcomes"][model_name]["vs_original_stdev"] = stdev

    # shut down opponent server
    close_env_process(env_process)
    print(result)

    chdir("..")
    # pwd is ~/
    print_json(result_file_name, result)

'''
example: python3 test_curve.py sl29_randNoAndB sl29 7 0.5 4 SepLayerGraph0_noAnd_B.json \
    True 1000 DepgraphJavaEnvVsMixedDef29N-v0 DepgraphJavaEnvVsMixedAtt29N-v0
'''
if __name__ == '__main__':
    if len(sys.argv) != 11:
        raise ValueError("Need 10 args: env_short_name_tsv, env_short_name_payoffs, " + \
                         "cur_epoch, old_strat_disc_fact, save_count, graph_name, " + \
                         "is_defender_net, runs_per_pair, env_name_vs_mixed_def, " + \
                         "env_name_vs_mixed_att")
    ENV_SHORT_NAME_TSV = sys.argv[1]
    ENV_SHORT_NAME_PAYOFFS = sys.argv[2]
    CUR_EPOCH = int(sys.argv[3])
    OLD_STRAT_DISC_FACT = float(sys.argv[4])
    SAVE_COUNT = int(sys.argv[5])
    GRAPH_NAME = sys.argv[6]
    IS_DEFENDER_NET = get_truth_value(sys.argv[7])
    RUNS_PER_PAIR = int(sys.argv[8])
    ENV_NAME_VS_MIXED_DEF = sys.argv[9]
    ENV_NAME_VS_MIXED_ATT = sys.argv[10]
    main(ENV_SHORT_NAME_TSV, ENV_SHORT_NAME_PAYOFFS, CUR_EPOCH, OLD_STRAT_DISC_FACT, \
        SAVE_COUNT, GRAPH_NAME, IS_DEFENDER_NET, RUNS_PER_PAIR, ENV_NAME_VS_MIXED_DEF, \
        ENV_NAME_VS_MIXED_ATT)