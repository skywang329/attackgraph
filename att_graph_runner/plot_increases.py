import sys
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
from pylab import savefig
from plot_strat_rounds import get_all_eq_from_files, get_round

def get_total_gain(prev_round_dict, cur_round_dict, cur_net_name):
    result = 0.0
    for strat, weight in cur_round_dict.items():
        if strat != cur_net_name:
            if strat in prev_round_dict:
                result += max(0, weight - prev_round_dict[strat])
            else:
                result += weight
    return result

def get_total_gain_missing_only(prev_round_dict, cur_round_dict, cur_net_name):
    result = 0.0
    for strat, weight in cur_round_dict.items():
        if strat != cur_net_name and strat not in prev_round_dict:
            result += weight
    return result

def get_network_round_to_name(round_dict):
    result = {}
    for strat in round_dict.keys():
        net_round = str(get_round(strat))
        if net_round not in result:
            result[net_round] = strat
    return result

def get_all_increases(round_dicts, is_missing_only):
    result = []
    for i in range(1, len(round_dicts)):
        prev_round_dict = round_dicts[i - 1]
        cur_round_dict = round_dicts[i]
        cur_rounds_to_names = get_network_round_to_name(cur_round_dict)
        cur_net_name = cur_rounds_to_names.get(str(i), None)
        if is_missing_only:
            total_gain = get_total_gain_missing_only(prev_round_dict, cur_round_dict, \
                cur_net_name)
        else:
            total_gain = get_total_gain(prev_round_dict, cur_round_dict, cur_net_name)
        result.append(total_gain)
    return result

def plot_increases(def_increases, att_increases, env_short_name_payoffs):
    fig, ax = plt.subplots()
    fig.set_size_inches(7, 4)

    my_lw = 2
    plt.plot(range(len(def_increases)), def_increases, lw=my_lw, label="Defender")
    plt.plot(range(len(att_increases)), att_increases, linestyle=':', lw=my_lw, \
        label='Attacker')
    plt.ylim((0, 1))

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    plt.ylabel("Old strategies' weight increase", fontsize=16)
    plt.xlabel('Training round', fontsize=16)
    my_title = "Random 30-node graph"
    if "s29" in env_short_name_payoffs:
        my_title = "Separate layers 29-node graph"
    plt.title(my_title, fontsize=20)
    ax.yaxis.set_ticks_position('left')
    ax.tick_params(labelsize=14)
    ax.legend()
    plt.tick_params(
        axis='x',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        top='off'         # ticks along the top edge are off
    )
    plt.tick_params(
        axis='y',          # changes apply to the y-axis
        which='both',      # both major and minor ticks are affected
        right='off'         # ticks along the right edge are off
    )
    plt.tight_layout()

    savefig(env_short_name_payoffs + "_increases.pdf")

def main(env_short_name_payoffs, env_short_name_tsv):
    def_eqs, att_eqs = get_all_eq_from_files(env_short_name_tsv)
    def_increases = get_all_increases(def_eqs, False)
    att_increases = get_all_increases(att_eqs, False)

    print("def increases: " + str(def_increases))
    print("att increases: " + str(att_increases))

    mean_def_increase = np.mean(def_increases)
    mean_att_increase = np.mean(att_increases)
    fmt = "{0:.2f}"
    print("mean def increase: " + fmt.format(mean_def_increase))
    print("mean att increase: " + fmt.format(mean_att_increase))

    plot_increases(def_increases, att_increases, env_short_name_payoffs)

    def_increases_missing_only = get_all_increases(def_eqs, True)
    att_increases_missing_only = get_all_increases(att_eqs, True)
    mean_def_increase_missing_only = np.mean(def_increases_missing_only)
    mean_att_increase_missing_only = np.mean(att_increases_missing_only)
    print("mean def increase missing only: " + fmt.format(mean_def_increase_missing_only))
    print("mean att increase missing only: " + fmt.format(mean_att_increase_missing_only))


'''
example: python3 plot_increases.py s29m1 s29m1_randNoAndB
'''
if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError("Need 2 args: env_short_name_payoffs, " + \
            "env_short_name_tsv")
    ENV_SHORT_NAME_PAYOFFS = sys.argv[1]
    ENV_SHORT_NAME_TSV = sys.argv[2]
    main(ENV_SHORT_NAME_PAYOFFS, ENV_SHORT_NAME_TSV)
