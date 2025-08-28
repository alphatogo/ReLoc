from model import *
from parser import *
from Node_selection import *
from data.load_datas import *

class Runner:
    def __init__(self, args, config):

        self.args = args
        self.config = config
        self.model = model(args)
        self.selection_method = Node_selection(args, config)


    def search(self, problem):
        seed_code = []

        
        
        self.args.seed_num = self.config["First_layer_num"]
        seed_code = self.model.seed_generate(problem, self.args)
        

        self.selection_method.add_node(seed_code, problem, self.model.self_score, self_reflection_function=self.model.self_reflection)

        seed_selected_node = self.selection_method.selection_from_seed_code()
        self.selection_method.node_expand(problem, seed_selected_node, self.model.self_reflection, self.model.self_debug, self.model.self_score, population=self.config["Population"] if "Population" in self.config else False)

        no_leaf_selected_node = seed_selected_node
        while len(self.selection_method.all_node) < self.selection_method.search_budget_node and no_leaf_selected_node:
            no_leaf_selected_node = self.selection_method.selection_from_not_leaf(no_leaf_selected_node)
            self.selection_method.node_expand(problem, no_leaf_selected_node, self.model.self_reflection,self.model.self_debug, self.model.self_score)

        final_commit_node = self.selection_method.final_commit_selection()
        return final_commit_node



if __name__ == '__main__':
    args = get_args()
    benchmark = load_data(args)
    for problem in benchmark:
        x = execution(args, ["", "fdsaf"], test_case=problem.public_test_case)
        x = execution(args, ["", "fdsaf"], test_case=problem.private_test_case)
