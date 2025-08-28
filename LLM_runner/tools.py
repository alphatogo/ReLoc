import re
def remove_comments_and_whitespace(code):
    cleaned_lines = []
    for line in code.split('\n'):
        line = re.sub(r'#.*$', '', line)
        line_script = line.strip()
        if not line_script:
            line = line_script
        if line:
            cleaned_lines.append(line)
    cleaned_code = '\n'.join(cleaned_lines)
    return cleaned_code


def code_extraction(answer):
    answer_inits = []
    for text in answer:

        outputlines = text.split("\n")
        indexlines = [i for i, line in enumerate(outputlines) if "```" in line]
        if len(indexlines) < 2:
            continue
        else:
            code = "\n".join(outputlines[indexlines[0] + 1: indexlines[1]])
            answer_inits.append(remove_comments_and_whitespace(code))

    return answer_inits

def code_extraction_debug(answer):
    answer_inits = []
    for text in answer:

        outputlines = text.split("\n")
        indexlines = [i for i, line in enumerate(outputlines) if "```" in line]
        if len(indexlines) < 2:
            answer_inits.append(remove_comments_and_whitespace(""))
        else:
            code = "\n".join(outputlines[indexlines[0] + 1: indexlines[1]])
            answer_inits.append(remove_comments_and_whitespace(code))

    return answer_inits


def observations_extraction(answer):
    pattern = r'\[OBSERVATION\](.*?)\[\\OBSERVATION\]'
    matches = []
    for text in answer:
        matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        pattern = r'\[OBSERVATION\]\s*(.*?)(?=\n\s*\[OBSERVATION\]|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        matches = [match.strip() for match in matches]
    
    
    return matches

def relfection_extraction(answer):

    explanation_list = []
    direction_list = []
    for text in answer:
        pattern = r'\[explanation\](.*?)\[/explanation\]'
        explanation = re.findall(pattern, text, re.DOTALL)

        if len(explanation) == 0:
            pattern = r'\[explanation\](.*?)(?=\[direction\]|\Z)'
            explanation = re.findall(pattern, text, re.DOTALL)

        explanation = explanation[0] if len(explanation) > 0 else None

        pattern = r'\[direction\](.*?)\[/direction\]'
        direction = re.findall(pattern, text, re.DOTALL)
        if len(direction) == 0:
            pattern = r'\[direction\](.*?)(?=\[direction\]|\Z)'
            direction = re.findall(pattern, text, re.DOTALL)
            # Clean up extracted directions if any found
            if len(direction) > 0:
                direction = [d.strip() for d in direction]
        direction = direction if len(direction) > 0 else None
        explanation_list.append(explanation)
        direction_list.append(direction)
    return explanation_list, direction_list

def get_all_paths(root_node):

    all_paths = []
    def dfs(node, current_path, depth):
      
        node_dict = {
            'code_content': node.code_content,
        }
        current_path.append(node_dict)
        if not node.children or depth > 10:
            all_paths.append(current_path[:])
        else:
            children_node = [child_node for child_node in node.children]
            for child in children_node:
                dfs(child, current_path[:], depth + 1)

    dfs(root_node, [], 0)

    return all_paths


def self_score_extraction(answer):
    reward = 0
    if type(answer) == list and len(answer) == 1:
        test = answer[0]
    else:
        test = answer
    pattern = r'<score>((?:.|\n)*?)</score>'
    matches = re.findall(pattern, test)

    if matches:
        try:
            reward = int(matches[-1].strip())
        except:
            reward = 0
    else:
        last_line = test.strip().split('\n')[-1]
        numbers = re.findall(r'\d+', last_line)

        if numbers and int(numbers[-1])>=0 and int(numbers[-1])<=10:
            reward = int(numbers[-1])
        else:
            reward = 0

    return reward

def test_case_extraction_debug(answers):
    test_cases = []
    test_pattern = r'<TEST>(.*?)</TEST>'
    pattern = r'^\{\s*"inputs":\s*\[.*?\],\s*"outputs":\s*\[.*?\],\s*"fn_name":\s*.*?\s*\}$'
    for answer in answers:

        matches = re.search(test_pattern, answer, re.DOTALL)
        if matches:
            try:
                content = matches.group(1).strip()
                if bool(re.match(pattern, content)):
                    test_cases.append(content)
            except:
                continue

    return test_cases
