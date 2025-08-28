from scenario_router import (
    build_prompt_benchmark,
    sort_and_extract_save_results,
    get_metrics,
)
from parser import get_args

from compute_code_generation_metrics import *

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def remove_comments_and_whitespace(code):
    cleaned_lines = []
    for line in code.split('\n'):
        # Remove single-line comments
        line = re.sub(r'#.*$', '', line)

        # Remove leading and trailing whitespace
        line_script = line.strip()
        if not line_script:
            line = line_script

        # Skip empty lines
        if line:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def create_temp_files(incorrect_code, revised_code, thread_id):
    """Create temporary files for the incorrect and revised code with thread-specific paths."""
    temp_dir = f'./tem_{thread_id}'
    os.makedirs(temp_dir, exist_ok=True)

    incorrect_path = os.path.join(temp_dir, "incorrect.py")
    revised_path = os.path.join(temp_dir, "revised.py")

    incorrect_code = remove_comments_and_whitespace(incorrect_code)
    revised_code = remove_comments_and_whitespace(revised_code)

    with open(incorrect_path, 'w') as f:
        f.write(incorrect_code)

    with open(revised_path, 'w') as f:
        f.write(revised_code)

    return incorrect_path, revised_path


def analyze_diff_file(file_path):
    """Analyze the diff file to count changes."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    original_changes = 0
    modified_lines = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if line.startswith('c'):  # Change command
            try:
                nums = line[1:].split()
                start, end = int(nums[0]), int(nums[1])
                original_changes += end - start + 1
            except:
                original_changes += 1
            i += 1
            while i < len(lines) and not lines[i].strip() == '.':
                if lines[i].strip():
                    modified_lines += 1
                i += 1

        elif line.startswith('d'):  # Delete command
            try:
                nums = line[1:].split()
                start, end = int(nums[0]), int(nums[1])
                original_changes += end - start + 1
            except:
                original_changes += 1

        elif line.startswith('a'):  # Add command
            i += 1
            while i < len(lines) and not lines[i].strip() == '.':
                if lines[i].strip():
                    modified_lines += 1
                i += 1
        else:
            print(f"No command match for line: {line}")

        i += 1

    return original_changes, modified_lines


def process_single_code(incorrect_code, thread_id):
    """Process a single code comparison with thread-specific temporary files."""
    if 'Revised_code' not in incorrect_code:
        return incorrect_code

    if not ('Revised_code_evaluation' in incorrect_code and incorrect_code['Revised_code_evaluation']):
        return incorrect_code

    try:
        incorrect = incorrect_code['Incorrect_code_content']
        revised_code = incorrect_code['Revised_code']

        incorrect_path, revised_path = create_temp_files(incorrect, revised_code, thread_id)
        diff_path = os.path.join(os.path.dirname(incorrect_path), "diff.txt")

        try:
            with open(diff_path, 'w') as f:
                process = subprocess.Popen(
                    ['diff', '-f', incorrect_path, revised_path],
                    stdout=f,
                    stderr=subprocess.PIPE
                )
                process.wait()

            original_changes, modified_lines = analyze_diff_file(diff_path)
            incorrect_code['revised_code_diff'] = {
                'original_changes': original_changes,
                'modified_lines': modified_lines
            }

        except subprocess.CalledProcessError as e:
            print(f"Diff command failed with error: {e}")
            incorrect_code['revised_code_diff'] = {
                'original_changes': 0,
                'modified_lines': 0
            }

        finally:
            # Clean up temporary files
            if os.path.exists(incorrect_path):
                os.remove(incorrect_path)
            if os.path.exists(revised_path):
                os.remove(revised_path)
            if os.path.exists(diff_path):
                os.remove(diff_path)
            if os.path.exists(os.path.dirname(incorrect_path)):
                os.rmdir(os.path.dirname(incorrect_path))

    except Exception as e:
        print(f"Error processing code in thread {thread_id}: {e}")
        incorrect_code['revised_code_diff'] = {
            'original_changes': 0,
            'modified_lines': 0
        }

    return incorrect_code


def diff():
    # Read the JSON file
    with open('./evaluation_claude_code.json', "r") as f:
        data = json.load(f)

    # Create a list of all code pairs that need to be processed
    all_codes = []
    for problem in data:
        if "incorrect_codes" in problem:
            all_codes.extend(problem["incorrect_codes"])

    # Process codes in parallel using ThreadPoolExecutor
    max_workers = min(32, len(all_codes))  # Limit maximum number of threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a partial function with thread IDs
        process_with_id = lambda code, tid: process_single_code(code, tid)

        # Map the processing function over all codes with thread IDs
        processed_codes = list(executor.map(
            process_with_id,
            all_codes,
            range(len(all_codes))
        ))

    # Update the original data structure with processed results
    code_index = 0
    for problem in data:
        if "incorrect_codes" in problem:
            num_codes = len(problem["incorrect_codes"])
            problem["incorrect_codes"] = processed_codes[code_index:code_index + num_codes]
            code_index += num_codes

    # Write the updated data back to the JSON file
    with open('./evaluation_claude_code_diff.json', 'w') as f:
        json.dump(data, f, indent=4)


def main():
    args = get_args()

    benchmark, _ = build_prompt_benchmark(args)

    with open(args.custom_output_file, "r") as f:
        data = json.load(f)

    compiler_input = []
    compiler_test_case = []
    current_problem = None
    count = 0
    for problem in data:

        revised_codes_list = []
        for incorrect_code in problem["incorrect_codes"]:
            if 'Revised_code' not in incorrect_code:
                break
            else:
                if incorrect_code["Revised_code"]:
                    revised_codes_list.append(incorrect_code["Revised_code"])

        if revised_codes_list:
            # if count > 1:
            #     break
            count += 1
            compiler_input.append(revised_codes_list)
            for bench in benchmark:
                if problem["problem"] == bench.question_title+'_'+bench.difficulty.value:
                    eval_samples = bench.get_evaluation_sample()
                    compiler_test_case.append(eval_samples)

    _, final_correct = codegen_metrics(
        compiler_test_case,
        compiler_input,
        num_process_evaluate=args.num_process_evaluate,
        timeout=args.timeout,
    )
    evaluation_json = []
    index_problem = 0
    for problem in data:
        # if index_problem > 1:
        #     break
        index_code = 0
        revised_codes_list = []
        if 'incorrect_codes' not in problem:
            evaluation_json.append(problem)
            continue
        incorrect_codes = []
        for incorrect_code in problem["incorrect_codes"]:
            if 'Revised_code' not in incorrect_code:
                evaluation_json.append(problem)
                break
            else:
                if incorrect_code["Revised_code"]:
                    revised_codes_list.append(incorrect_code["Revised_code"])
                    incorrect_code["Revised_code_evaluation"] = bool(final_correct[index_problem][index_code])
                    # incorrect_code["Revised_code_evaluation"] = bool(False)
                    incorrect_codes.append(incorrect_code)
                    index_code += 1
                else:
                    incorrect_codes.append(incorrect_code)

        if revised_codes_list:
            problem["incorrect_codes"] = incorrect_codes
            evaluation_json.append(problem)
            index_problem += 1


    print(final_correct)
    with open('./evaluation_claude_code.json', 'w') as f:
        json.dump(evaluation_json, f, indent=4)




def analyze_distributions():
    with open('./evaluation_claude_code_diff.json', "r") as f:
        data = json.load(f)

    pairs = []
    for problem in data:
        if "incorrect_codes" in problem:
            for incorrect_code in problem["incorrect_codes"]:
                if ('Revised_code_evaluation' in incorrect_code and
                        incorrect_code['Revised_code_evaluation'] and
                        'revised_code_diff' in incorrect_code and
                        'Correct_code' in incorrect_code):
                    revised = incorrect_code['revised_code_diff']['original_changes']
                    correct = incorrect_code['Correct_code']['original_changes']
                    if revised <= 20 and correct <= 20:
                        pairs.append((revised, correct))

    revised_changes, correct_changes = zip(*pairs)
    bins = np.arange(0, 21, 1)

    revised_hist = np.histogram(revised_changes, bins=bins)[0]
    correct_hist = np.histogram(correct_changes, bins=bins)[0]

    plt.figure(figsize=(12, 6))
    x = np.arange(0, 20, 1)

    plt.plot(x, revised_hist, 'b-', marker='o', label='Revised Code', linewidth=2)
    plt.plot(x, correct_hist, 'g-', marker='o', label='Correct Code', linewidth=2)

    # Add count labels
    for i in range(len(x)):
        if revised_hist[i] > 0:
            plt.text(x[i], revised_hist[i], str(int(revised_hist[i])),
                     ha='center', va='bottom', color='blue')
        if correct_hist[i] > 0:
            plt.text(x[i], correct_hist[i], str(int(correct_hist[i])),
                     ha='center', va='top', color='green')

    plt.title('Distribution of Changes in Code')
    plt.xlabel('Number of Changes')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    total_pairs = len(pairs)
    less_than_count = sum(1 for r, c in pairs if r < c)
    proportion = less_than_count / total_pairs if total_pairs > 0 else 0

    stats_text = f"Total pairs: {total_pairs}\nRevised < Correct: {less_than_count}\nProportion: {proportion:.2%}"
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig('code_changes_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    analyze_distributions()




if __name__ == "__main__":
    # main()
    # diff()
    analyze_distributions()