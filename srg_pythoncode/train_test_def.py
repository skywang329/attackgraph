import sys
import subprocess
import time
import os.path

def start_and_return_env_process(graph_name):
    cmd = "exec java -jar ../depgraphpy4jdefvseither/depgraphpy4jdefvsnetorheuristic.jar " \
        + graph_name
    env_process = subprocess.Popen(cmd, shell=True)
    sleep_sec = 5
    # wait for Java server to start
    time.sleep(sleep_sec)
    return env_process

def close_env_process(env_process):
    sleep_sec = 5
    time.sleep(sleep_sec)
    env_process.kill()

def run_training(env_short_name, new_epoch, env_name_att_net):
    cmd_list = ["python3", "train_dg_java_mlp_def_vs_mixed.py", env_name_att_net, \
        str(new_epoch)]
    def_out_name = "defVMixed_" + env_short_name + "_epoch" + str(new_epoch) + ".txt"
    if os.path.isfile(def_out_name):
        print("Skipping: " + def_out_name + " already exists.")
        return
    with open(def_out_name, "w") as file:
        subprocess.call(cmd_list, stdout=file)

def run_evaluation(env_short_name, new_epoch, env_name_att_net):
    cmd_list = ["python3", "enjoy_depgraph_data_vs_mixed.py", env_name_att_net, \
        env_short_name, str(new_epoch)]
    def_out_name_enj = "def_" + env_short_name + "_randNoAndB_epoch" + str(new_epoch) + \
        ".txt"
    if os.path.isfile(def_out_name_enj):
        print("Skipping: " + def_out_name_enj + " already exists.")
        return
    with open(def_out_name_enj, "w") as file:
        subprocess.call(cmd_list, stdout=file)

def main(graph_name, env_short_name, new_epoch, env_name_att_net):
    env_process = start_and_return_env_process(graph_name)
    run_training(env_short_name, new_epoch, env_name_att_net)
    run_evaluation(env_short_name, new_epoch, env_name_att_net)
    close_env_process(env_process)

'''
example: python3 train_test_def.py SepLayerGraph0_noAnd_B.json sl29 16 \
    DepgraphJavaEnvVsMixedAtt29N-v0
'''
if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise ValueError("Need 4 args: graph_name, env_short_name, new_epoch, " + \
            "env_name_att_net")
    GRAPH_NAME = sys.argv[1]
    ENV_SHORT_NAME = sys.argv[2]
    NEW_EPOCH = int(sys.argv[3])
    ENV_NAME_ATT_NET = sys.argv[4]
    main(GRAPH_NAME, ENV_SHORT_NAME, NEW_EPOCH, ENV_NAME_ATT_NET)