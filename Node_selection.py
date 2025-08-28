
from feedback.Reward_model import Reward_model
import random
from feedback.execution import execution
import copy

class Node:
    def __init__(self, code_content, args, config, result_public=None, result_private=None, reward=None, self_score=None, weight_dict=None, public_test_case=None):

        self.code_content = code_content
        self.public_pass_rate = 0
        if result_public:
            self.execution_results_public = all(execution_result == True for execution_result in result_public[0])
            self.public_pass_count = sum(1 for execution_results in result_public[0] if execution_results == True)
            self.public_pass_rate = self.public_pass_count / public_test_case["number"]
        if result_private:
            self.execution_results_private = all(execution_result == True for execution_result in result_private[0])
            self.private_pass_count = sum(1 for execution_results in result_private[0] if execution_results == True)

        self.metadata = result_public[1] if result_public else None
        self.reward = 0 if reward is None else reward
        self.self_score = 0 if self_score is None else self_score
        self.config = config
        self.args = args
        self.expand_budget = config["expand_budget"]
        self.expand_num = 0
        self.expand_num_per_call = config["expand_num_per_call"]

        self.explanation = ""
        self.expand_direction = []
        self.used_direction = []
        self.children = []
        self.parent = []


        self.selection_score = self.public_pass_rate*weight_dict["Test case"] + self.reward*weight_dict["Reward model"] + self.self_score*weight_dict["Self score"]

        self.leaf = True


    def modify_node(self, explanation, directions):
        self.explanation += explanation if explanation else ""
        self.expand_direction += directions if directions else []
        if self.args.config_path == "GEN":
            self.expand_budget = max(self.config["expand_budget"], len(self.expand_direction))
        else:
            self.expand_budget = min(self.config["expand_budget"], len(self.expand_direction))


class Node_selection:
    def __init__(self, args, config):
        self.args = args
        self.device = self.args.device
        self.choose_method = config["Selection_method"]
        self.select_top_k = config["select_top_k"]
        if "Reward model" in self.choose_method:
            self.rm = Reward_model(args)
        self.selection_node_list = []
        self.refined_node_list = []
        self.all_node = []

        self.weight_dict = config["Selection_reward_weight"]
        self.pass_n = config["Pass@n"]
        self.config = config
        self.best_node = Node("", args, config, weight_dict=self.weight_dict)
        self.root_node = Node("", args, config, weight_dict=self.weight_dict)
        self.search_budget_node = config["search_budget_node"]

    def selection_method_reset(self):
        
        self.selection_node_list = []
        self.refined_node_list = []
        self.all_node = []
        self.all_code_content = []
        self.best_node = Node("", self.args, self.config, weight_dict=self.config["Selection_reward_weight"])

    def final_commit_selection(self):
        sorted_nodes = sorted(self.all_node, key=lambda x: x.selection_score, reverse=True)
        top_k = min(self.pass_n, len(sorted_nodes))
        return sorted_nodes[:top_k]

    def selection_from_seed_code(self):
        if self.args.config_path != "GEN":
            seed_nodes = self.root_node.children
            sorted_seed_node = sorted(seed_nodes, key=lambda x: x.selection_score, reverse=True)
            top_k = min(self.select_top_k, len(sorted_seed_node))
            return sorted_seed_node[:top_k]
        else:
            all_node = []
            for node in self.all_node:
                if node not in all_node and len(node.used_direction) < node.expand_budget:
                    all_node.append(node)

            sorted_seed_node = sorted(all_node, key=lambda x: x.selection_score, reverse=True)
            top_k = min(self.select_top_k, len(sorted_seed_node))
            return sorted_seed_node[:top_k]


    def selection_from_not_leaf(self, seed_selected_node_list):
        if self.args.config_path != "GEN":
            selection_node_list = set()
            selection_node_list.update(child for node in seed_selected_node_list for child in node.children)
            selection_node_list.update(seed_selected_node_list)
            sorted_seed_node = sorted(
                [x for x in selection_node_list if x.expand_num < x.expand_budget],
                key=lambda x: x.selection_score,
                reverse=True
            )

            if len(sorted_seed_node) == 0:
                sorted_seed_node = sorted(
                    [x for x in self.all_node if x.expand_num < x.expand_budget],
                    key=lambda x: x.selection_score,
                    reverse=True
                )
                if len(sorted_seed_node) == 0:
                    return []

            top_k = min(self.select_top_k, len(sorted_seed_node))
            return sorted_seed_node[:top_k]
        else:
            all_node = []
            for node in self.all_node:
                if node not in all_node and len(node.used_direction) < node.expand_budget:
                    all_node.append(node)

            sorted_seed_node = sorted(all_node, key=lambda x: x.selection_score, reverse=True)
            top_k = min(self.select_top_k, len(sorted_seed_node))
            return sorted_seed_node[:top_k]


    def add_node(self, code_contents, problem, self_score_function=None, current_node=None, answer_strategy_descriptions=None, self_reflection_function=None):
        try:
            execution_results_public = execution(self.args, code_contents, test_case=problem.public_test_case)
        except:
            execution_results_public = [[False], ""]
        execution_results_private = execution(self.args, code_contents, test_case=problem.private_test_case)

        answer_strategy_descriptions = answer_strategy_descriptions if answer_strategy_descriptions else [""] * len(code_contents)

        node_list = []
        for code_content, result_public, result_private, answer_strategy_description in zip(code_contents, execution_results_public, execution_results_private, answer_strategy_descriptions):

            same_node = [node for node in self.all_node if node.code_content == code_content]
            if not same_node:
                self_reward = self_score_function(problem, code_content) if "Self score" in self.choose_method else 0
                reward = self.rm.reward(problem, [code_content]) if "Reward model" in self.choose_method else [0]
                node = Node(code_content, self.args, self.config, result_public, result_private, reward[0], self_reward, self.weight_dict, problem.public_test_case)

            else:
                node = same_node[0]

            self.all_node.append(node)
            node.parent += [current_node] if current_node else []
            node_list.append(node)

        if not current_node:
            self.root_node.children += node_list
            self.root_node.expand_num += len(node_list)
        else:
            current_node.children += node_list
            current_node.expand_num += len(node_list)


    def node_expand(self, problem, selected_nodes, self_reflection_function, self_debug_function, self_score_function, population=True):
        if "GEN" in self.args.config_path and population:
            answer, answer_strategy_description = self_debug_function(problem, selected_nodes, GEN=True)
            self.add_node([answer], problem, self_score_function, current_node=None,
                          answer_strategy_descriptions=[answer_strategy_description])
        else:
            for selected_node in selected_nodes:
                for _ in range(selected_node.expand_num_per_call):
                    if selected_node.expand_num >= selected_node.expand_budget:
                        break

                    if self.args.neighbor_strategy:
                        self_reflection_function(problem, selected_node)

                    answer, answer_strategy_description = self_debug_function(problem, selected_node)
                    selected_node.used_direction.append(answer_strategy_description)
                    self.add_node([answer], problem, self_score_function, current_node=selected_node, answer_strategy_descriptions=[answer_strategy_description])





class Debug_tree:
    def __init__(self, args):
        self.args = args
        self.device = self.args.device
        self.seed_node_list = []
        self.best_node = Node("", args)
        self.current_node = []
        self.code_node_map = {}

    def initial_debug_tree(self, seed_code, reward_list, execution_results_all):
        for code, reward, execution_results in zip(seed_code, reward_list, execution_results_all):
            node = Node(code, self.args, execution=execution_results, reward=reward)
            self.seed_node_list.append(node)
            self.code_node_map[code] = node
        self.current_node = self.seed_node_list
        return self.seed_node_list

    def update(self, refined_code_list, refined_code_index, reward_list_all, execution_results_all):
        for node in self.current_node:
            children_code = refined_code_list[refined_code_index[node][0]:refined_code_index[node][1]]
            reward_list = reward_list_all[refined_code_index[node][0]:refined_code_index[node][1]]
            execution_results_node = execution_results_all[refined_code_index[node][0]:refined_code_index[node][1]]

            if children_code:
                node.leaf = False
            for child_code, reward, execution_results in zip(children_code, reward_list, execution_results_node):
                if child_code == "":
                    continue
                if child_code in self.code_node_map and child_code not in node.children:
                    node.children.append(self.code_node_map[child_code].code_content)
                elif child_code in node.children:
                    continue
                else:
                    child_node = Node(child_code, self.args, execution=execution_results, reward=reward)
                    if child_node.execution_results==False:
                        child_node.leaf = False
                    self.code_node_map[child_code] = child_node
                    node.children.append(child_node.code_content)

        self.weighted_stratified_sampling()

    def weighted_stratified_sampling(self):
      
        candidate_nodes = []
        for code, node in self.code_node_map.items():
            if not node.children and node.execution_results == False:
                candidate_nodes.append(node)

        if len(candidate_nodes) <= 150:
            self.current_node = candidate_nodes
            return

    
        candidate_nodes.sort(key=lambda x: x.pass_count, reverse=True)

  
        n = len(candidate_nodes)
        first_third = n // 3
        second_third = 2 * n // 3

        high_priority = candidate_nodes[:first_third]
        medium_priority = candidate_nodes[first_third:second_third]
        low_priority = candidate_nodes[second_third:]

        def weighted_sample(nodes, sample_size):
            if not nodes:
                return []
          
            weights = [1 / (i + 1) for i in range(len(nodes))]
      
            total = sum(weights)
            weights = [w / total for w in weights]
            return random.choices(nodes, weights=weights, k=min(sample_size, len(nodes)))

        selected_nodes = []
        selected_nodes.extend(weighted_sample(high_priority, 80)) 
        selected_nodes.extend(weighted_sample(medium_priority, 50))  
        selected_nodes.extend(weighted_sample(low_priority, 20))

 
        remaining = 150 - len(selected_nodes)
        if remaining > 0:
            remaining_pool = [x for x in high_priority if x not in selected_nodes]
            if remaining_pool:
                selected_nodes.extend(weighted_sample(remaining_pool, remaining))

        self.current_node = selected_nodes

    def get_all_paths(self):

        all_paths = []

        def dfs(node, current_path, depth):
           
            node_dict = {
                'code_content': node.code_content,
                'reward': node.reward,
                'execution_results': node.execution_results,
                'leaf': node.leaf,
                'pass_count': node.pass_count,
                'depth': depth
            }



            current_path.append(node_dict)

        
            if node.leaf or depth > 5:
                all_paths.append(current_path[:])
            else:

                children_node = [self.code_node_map[child_code] for child_code in node.children]
                for child in children_node:
                  
                    dfs(child, current_path[:], depth + 1)

        
        for seed_node in self.seed_node_list:
            dfs(seed_node, [], 0)

        return all_paths





