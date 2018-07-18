'''
Run the first epoch and part of second epoch of training for robustified double-oracle
method, where each successful training session is followed by fine-tuning against a mixture
of previous opponent equilibria for robustness.
Runs the second epoch until after fine-tuning, when a human must assist by deciding which
network (the trained one or a fine-tuned version) to proceed with for attacker and defender.
'''
import sys
import datetime
import subprocess
from os import chdir
import os.path
import pythoncode.check_if_beneficial as check
from add_new_data import get_add_data_result_file_name

def run_gambit(game_number, cur_epoch):
    '''
    Call a script to find a Nash equilibrium of the current game.
    '''
    cmd_list = ["python3", "gambit_analyze.py", str(game_number), str(cur_epoch)]
    subprocess.call(cmd_list)

def run_create_tsv(game_number, cur_epoch, env_short_name_tsv):
    '''
    Run a script to extract the current equilibrium strategies to TSV files.
    '''
    cmd_list = ["python3", "create_tsv_files.py", str(game_number), str(cur_epoch), \
        env_short_name_tsv]
    subprocess.call(cmd_list)

def run_update_strats(env_short_name_tsv, env_short_name_payoffs, new_epoch):
    '''
    Run a script to update the config files for the Gym environments to reference the new
    equilibrium strategies' TSV files.
    '''
    cmd_list = ["python3", "update_opponent_strats.py", env_short_name_payoffs, \
        env_short_name_tsv, str(new_epoch)]
    subprocess.call(cmd_list)

def run_gen_def_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        def_payoff_count, env_short_name_payoffs, graph_name, new_epoch):
    '''
    Run a script to evaluate each defender strategy against the current equilibrium
    opponent, and record the mean payoff of the best one.
    '''
    cmd_list = ["python3", "gen_def_payoffs.py", env_name_def_net, env_name_att_net, \
        env_name_both, str(def_payoff_count), env_short_name_payoffs, graph_name, \
        str(new_epoch)]
    subprocess.call(cmd_list)

def run_gen_att_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        att_payoff_count, env_short_name_payoffs, graph_name, new_epoch):
    '''
    Run a script to evaluate each attacker strategy against the current equilibrium
    opponent, and record the mean payoff of the best one.
    '''
    cmd_list = ["python3", "gen_att_payoffs.py", env_name_def_net, env_name_att_net, \
        env_name_both, str(att_payoff_count), env_short_name_payoffs, graph_name, \
        str(new_epoch)]
    subprocess.call(cmd_list)

def run_train_test_def(graph_name, env_short_name_payoffs, new_epoch, \
    env_name_vs_mixed_att):
    '''
    Train a defender net against the current equilibrium opponent, and evaluate the mean
    payoff of the learned net.
    '''
    cmd_list = ["python3", "train_test_def.py", graph_name, env_short_name_payoffs, \
        str(new_epoch), env_name_vs_mixed_att]
    subprocess.call(cmd_list)

def run_train_test_att(graph_name, env_short_name_payoffs, new_epoch, \
    env_name_vs_mixed_def):
    '''
    Train a attacker net against the current equilibrium opponent, and evaluate the mean
    payoff of the learned net.
    '''
    cmd_list = ["python3", "train_test_att.py", graph_name, env_short_name_payoffs, \
        str(new_epoch), env_name_vs_mixed_def]
    subprocess.call(cmd_list)

def get_check_if_beneficial(env_short_name_payoffs, new_epoch, is_def):
    '''
    Check if the newly-trained strategy net (defender or attacker) yielded a higher mean
    payoff against the current equilibrium opponent than the best previous strategy of the
    same role.
    '''
    return check.check_for_cli(env_short_name_payoffs, new_epoch, is_def)

def run_gen_new_cols(env_name_def_net, env_name_att_net, env_name_both, new_col_count, \
    new_epoch, env_short_name_payoffs, def_model_to_add, att_model_to_add, graph_name):
    '''
    Evaluate the mean payoff for self and opponent of the new defender and attacker nets
    (whichever were beneficial deviations) against each opponent strategy, for augmenting
    the game's payoff matrix.
    '''
    cmd_list = ["python3", "generate_new_cols_curve.py", env_name_def_net, \
        env_name_att_net, env_name_both, str(new_col_count), str(new_epoch), \
        env_short_name_payoffs, str(def_model_to_add), str(att_model_to_add), graph_name]
    subprocess.call(cmd_list)

def run_append_net_names(env_short_name_payoffs, def_model_to_add, att_model_to_add):
    '''
    Add the names of the new attacker and defender nets (whichever were beneficial
    deviations) to the lists of network strategies in the game.
    '''
    cmd_list = ["python3", "append_net_names_curve.py", env_short_name_payoffs, \
        str(def_model_to_add), str(att_model_to_add)]
    subprocess.call(cmd_list)

def run_add_new_data(game_number, env_short_name_payoffs, new_epoch):
    '''
    Add the data on payoffs with the new beneficially deviating
    strategy/strategies to the game's Json file.
    '''
    cmd_list = ["python3", "add_new_data.py", str(game_number), env_short_name_payoffs, \
        str(new_epoch)]
    subprocess.call(cmd_list)

def run_retrain_def(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_att):
    '''
    Fine-tune a defender net against a mixture of previous opponents, and save the resulting
    net.
    '''
    cmd_list = ["python3", "retrain_def.py", graph_name, \
        env_short_name_payoffs, str(new_epoch), env_name_vs_mixed_att]
    subprocess.call(cmd_list)

def run_retrain_att(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_def):
    '''
    Fine-tune an attacker net against a mixture of previous opponents,
    and save the resulting net.
    '''
    cmd_list = ["python3", "retrain_att.py", graph_name,\
        env_short_name_payoffs, str(new_epoch), env_name_vs_mixed_def]
    subprocess.call(cmd_list)

def run_test_curve(env_short_name_tsv, env_short_name_payoffs, cur_epoch, \
    old_strat_disc_fact, save_count, graph_name, is_defender_net, runs_per_pair, \
    env_name_vs_mixed_def, env_name_vs_mixed_att):
    '''
    Fine-tune the recently-trained network against a weighted mean of previous opponent
    equilibrium strategies, and evaluate the result of the current and fine-tuned network
    versions.
    '''
    cmd_list = ["python3", "test_curve.py", env_short_name_tsv, env_short_name_payoffs, \
        str(cur_epoch), str(old_strat_disc_fact), str(save_count), graph_name, \
        str(is_defender_net), str(runs_per_pair), env_name_vs_mixed_def, \
        env_name_vs_mixed_att]
    subprocess.call(cmd_list)

def get_def_model_name(env_short_name_payoffs, new_epoch):
    ''' Get name of the defender network to generate. '''
    return "dg_" + env_short_name_payoffs + "_dq_mlp_rand_epoch" + str(new_epoch) + ".pkl"

def get_att_model_name(env_short_name_payoffs, new_epoch):
    ''' Get name of the attacker network to generate. '''
    return "dg_" + env_short_name_payoffs + "_dq_mlp_rand_epoch" + str(new_epoch) + \
        "_att.pkl"

def run_init_epoch(game_number, env_short_name_tsv, env_short_name_payoffs, \
    env_name_def_net, \
    env_name_att_net, env_name_both, def_payoff_count, att_payoff_count, graph_name, \
    env_name_vs_mixed_def, env_name_vs_mixed_att, new_col_count, old_strat_disc_fact, \
    save_count, runs_per_pair):
    '''
    Run the first epoch (epoch 0) of training. If no beneficial deviation is found, stop.
    Otherwise, begin the next epoch (epoch 1) of training, and stop after the attacker and
    defender nets have been trained, fine-tuned against the previous equilibrium, and the
    trained and fine-tuned nets have been evaluated against the current and previous
    equilibria. (The human can then choose which attacker and defender nets to add to the
    game.)
    '''
    cur_epoch = 0
    new_epoch = 1
    # pwd is ~/
    result_file_name = get_add_data_result_file_name(game_number, new_epoch + 1)
    if os.path.isfile(result_file_name):
        raise ValueError("Cannot run init: " + result_file_name + " already exists.")

    print("\tWill run gambit, epoch: " + str(cur_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # get Nash equilibrium of current strategies
    run_gambit(game_number, cur_epoch)
    # create TSV file for current attacker and defender equilibrium strategies
    run_create_tsv(game_number, cur_epoch, env_short_name_tsv)

    chdir("pythoncode")
    # pwd is ~/pythoncode
    # set the mixed-strategy opponents to use current TSV file strategies
    run_update_strats(env_short_name_tsv, env_short_name_payoffs, new_epoch)
    print("\tWill get def payoffs, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # sample and estimate mean payoff of each defender strategy vs. new attacker equilibrium
    run_gen_def_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        def_payoff_count, env_short_name_payoffs, graph_name, new_epoch)
    print("\tWill get att payoffs, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # sample and estimate mean payoff of each attacker strategy vs. new defender equilibrium
    run_gen_att_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        att_payoff_count, env_short_name_payoffs, graph_name, new_epoch)
    print("\tWill train and test defender, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # train defender network against current attacker equilibrium, and sample its payoff
    run_train_test_def(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_att)
    print("\tWill train and test attacker, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # train attacker network against current defender equilibrium, and sample its payoff
    run_train_test_att(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_def)

    # check if new defender network is beneficial deviation from old equilibrium
    is_def_beneficial = get_check_if_beneficial(env_short_name_payoffs, new_epoch, True)
    # check if new attacker network is beneficial deviation from old equilibrium
    is_att_beneficial = get_check_if_beneficial(env_short_name_payoffs, new_epoch, False)

    if not is_def_beneficial and not is_att_beneficial:
        # neither network beneficially deviates, so stop
        print("\tConverged after round: " + str(new_epoch), flush=True)
        return False

    print("\tWill generate new columns, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # sample payoff of each new network (if it beneficially deviates) against all opponent
    # strategies
    def_model_to_add = None
    if is_def_beneficial:
        def_model_to_add = get_def_model_name(env_short_name_payoffs, new_epoch)
    att_model_to_add = None
    if is_att_beneficial:
        att_model_to_add = get_att_model_name(env_short_name_payoffs, new_epoch)
    run_gen_new_cols(env_name_def_net, env_name_att_net, env_name_both, new_col_count, \
        new_epoch, env_short_name_payoffs, def_model_to_add, att_model_to_add, graph_name)
    # append name of each new network (if it beneficially deviates) to list of networks to
    # use in equilibrium search
    run_append_net_names(env_short_name_payoffs, def_model_to_add, att_model_to_add)

    chdir("..")
    # pwd is ~/
    # add new payoff data to game object (from new beneficially deviating network(s))
    run_add_new_data(game_number, env_short_name_payoffs, new_epoch)

    print("\tWill continue after round: " + str(new_epoch), flush=True)

    cur_epoch += 1
    new_epoch += 1

    print("\tWill run gambit, epoch: " + str(cur_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # get Nash equilibrium of current strategies
    run_gambit(game_number, cur_epoch)
    # create TSV file for current attacker and defender equilibrium strategies
    run_create_tsv(game_number, cur_epoch, env_short_name_tsv)

    chdir("pythoncode")
    # pwd is ~/pythoncode
    # set the mixed-strategy opponents to use current TSV file strategies
    run_update_strats(env_short_name_tsv, env_short_name_payoffs, new_epoch)
    print("\tWill get def payoffs, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # sample and estimate mean payoff of each defender strategy vs. new attacker equilibrium
    run_gen_def_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        def_payoff_count, env_short_name_payoffs, graph_name, new_epoch)
    print("\tWill get att payoffs, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # sample and estimate mean payoff of each attacker strategy vs. new defender equilibrium
    run_gen_att_payoffs(env_name_def_net, env_name_att_net, env_name_both, \
        att_payoff_count, env_short_name_payoffs, graph_name, new_epoch)
    print("\tWill train and test defender, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # train defender network against current attacker equilibrium, and sample its payoff
    run_train_test_def(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_att)
    print("\tWill train and test attacker, epoch: " + str(new_epoch)+ ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # train attacker network against current defender equilibrium, and sample its payoff
    run_train_test_att(graph_name, env_short_name_payoffs, new_epoch, env_name_vs_mixed_def)

    # check if new defender network is beneficial deviation from old equilibrium
    is_def_beneficial = get_check_if_beneficial(env_short_name_payoffs, new_epoch, True)
    # check if new attacker network is beneficial deviation from old equilibrium
    is_att_beneficial = get_check_if_beneficial(env_short_name_payoffs, new_epoch, False)

    if not is_def_beneficial and not is_att_beneficial:
        # neither network beneficially deviates, so stop
        print("\tConverged after round: " + str(new_epoch), flush=True)
        return False

    chdir("..")
    # pwd is ~/
    if is_def_beneficial:
        # should fine-tune net defender network against previous equilibria.
        print("\tWill fine-tune def, epoch: " + str(new_epoch)+ ", time: " + \
            str(datetime.datetime.now()), flush=True)
        chdir("pythoncode")
        # pwd is ~/pythoncode
        run_retrain_def(graph_name, env_short_name_payoffs, new_epoch, \
            env_name_vs_mixed_att)

        print("\tWill get def curve, epoch: " + str(new_epoch)+ ", time: " + \
            str(datetime.datetime.now()), flush=True)
        is_defender_net = True
        chdir("..")
        # pwd is ~/
        run_test_curve(env_short_name_tsv, env_short_name_payoffs, cur_epoch, \
            old_strat_disc_fact, save_count, graph_name, is_defender_net, runs_per_pair, \
            env_name_vs_mixed_def, env_name_vs_mixed_att)
    if is_att_beneficial:
        # should fine-tune net attacker network against previous equilibria.
        print("\tWill fine-tune att, epoch: " + str(new_epoch)+ ", time: " + \
            str(datetime.datetime.now()), flush=True)
        chdir("pythoncode")
        # pwd is ~/pythoncode
        run_retrain_att(graph_name, env_short_name_payoffs, new_epoch, \
            env_name_vs_mixed_def)

        print("\tWill get att curve, epoch: " + str(new_epoch)+ ", time: " + \
            str(datetime.datetime.now()), flush=True)
        is_defender_net = False
        chdir("..")
        # pwd is ~/
        run_test_curve(env_short_name_tsv, env_short_name_payoffs, cur_epoch, \
            old_strat_disc_fact, save_count, graph_name, is_defender_net, runs_per_pair, \
            env_name_vs_mixed_def, env_name_vs_mixed_att)
    return True

def main(game_number, env_short_name_tsv, env_short_name_payoffs, \
        env_name_def_net, env_name_att_net, \
        env_name_both, def_payoff_count, att_payoff_count, graph_name, \
        env_name_vs_mixed_def, env_name_vs_mixed_att, new_col_count, old_strat_disc_fact, \
        save_count, runs_per_pair):
    '''
    Call method to run first epoch (epoch 0), and beginning of second epoch (epoch 1).
    '''
    if old_strat_disc_fact <= 0.0 or old_strat_disc_fact > 1.0:
        raise ValueError("old_strat_disc_fact must be in (0, 1]: " + \
            str(old_strat_disc_fact))
    if save_count < 1:
        raise ValueError("save_count must be >= 1: " + str(save_count))
    if runs_per_pair < 2:
        raise ValueError("runs_per_pair must be >= 2: " + str(runs_per_pair))

    # first epoch is always 0
    my_epoch = 0
    print("\tWill run epoch: " + str(my_epoch) + ", time: " + \
        str(datetime.datetime.now()), flush=True)
    # indicates whether a beneficial deviation was found
    should_continue = run_init_epoch(game_number, env_short_name_tsv, \
        env_short_name_payoffs, env_name_def_net, env_name_att_net, env_name_both, \
        def_payoff_count, \
        att_payoff_count, graph_name, env_name_vs_mixed_def, env_name_vs_mixed_att, \
        new_col_count, old_strat_disc_fact, save_count, runs_per_pair)
    if should_continue:
        # proceed from epoch 1
        print("\tShould continue from epoch: 1, time: " + \
            str(datetime.datetime.now()), flush=True)
    else:
        # did not find beneficial deviation from initial equilibrium
        print("\tConverged in epoch 0, time: " + str(datetime.datetime.now()), flush=True)

'''
example: python3 master_dq_runner_curve_init.py 3013 sl29_randNoAndB sl29 \
    DepgraphJava29N-v0 DepgraphJavaEnvAtt29N-v0 DepgraphJavaEnvBoth29N-v0 100 400 \
    SepLayerGraph0_noAnd_B.json DepgraphJavaEnvVsMixedDef29N-v0 \
    DepgraphJavaEnvVsMixedAtt29N-v0 400 0.5 4 1000

'''
if __name__ == '__main__':
    if len(sys.argv) != 16:
        raise ValueError("Need 15 args: game_number, env_short_name_tsv, " + \
            "env_short_name_payoffs, " + \
            "env_name_def_net, env_name_att_net, env_name_both, def_payoff_count, " + \
            "att_payoff_count, graph_name, env_name_vs_mixed_def, "  + \
            "env_name_vs_mixed_att, new_col_count, " + \
            "old_strat_disc_fact, save_count, runs_per_pair")
    GAME_NUMBER = int(sys.argv[1])
    ENV_SHORT_NAME_TSV = sys.argv[2]
    ENV_SHORT_NAME_PAYOFFS = sys.argv[3]
    ENV_NAME_DEF_NET = sys.argv[4]
    ENV_NAME_ATT_NET = sys.argv[5]
    ENV_NAME_BOTH = sys.argv[6]
    DEF_PAYOFF_COUNT = int(sys.argv[7])
    ATT_PAYOFF_COUNT = int(sys.argv[8])
    GRAPH_NAME = sys.argv[9]
    ENV_NAME_VS_MIXED_DEF = sys.argv[10]
    ENV_NAME_VS_MIXED_ATT = sys.argv[11]
    NEW_COL_COUNT = int(sys.argv[12])
    OLD_STRAT_DISC_FACT = float(sys.argv[13])
    SAVE_COUNT = int(sys.argv[14])
    RUNS_PER_PAIR = int(sys.argv[15])
    main(GAME_NUMBER, ENV_SHORT_NAME_TSV, ENV_SHORT_NAME_PAYOFFS, \
        ENV_NAME_DEF_NET, ENV_NAME_ATT_NET, \
        ENV_NAME_BOTH, DEF_PAYOFF_COUNT, ATT_PAYOFF_COUNT, GRAPH_NAME, \
        ENV_NAME_VS_MIXED_DEF, ENV_NAME_VS_MIXED_ATT, NEW_COL_COUNT, \
        OLD_STRAT_DISC_FACT, SAVE_COUNT, RUNS_PER_PAIR)