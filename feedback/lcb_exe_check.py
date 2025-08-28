import tempfile
import subprocess
import os
from typing import List, Dict


def run_single_test(code: str, input_data: str) -> str:
    """运行单个测试用例"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file_name = f.name

    try:
       
        process = subprocess.Popen(
            ['python', temp_file_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        
        stdout, stderr = process.communicate(input_data)

        
        return stderr.strip() if stderr else stdout.strip()

    finally:
        
        os.unlink(temp_file_name)


def run_all_tests(code_list: List[str], test_cases: Dict) -> List[Dict]:
    
    results = []


    for code_index, code in enumerate(code_list):
        code_result = {
            'code_index': code_index,
            'test_results': []
        }

       
        for case_index in range(len(test_cases['inputs'])):
            input_data = test_cases['inputs'][case_index]
            expected_output = test_cases['outputs'][case_index]

       
            actual_output = run_single_test(code, input_data)

     
            test_result = {
                'test_case_index': case_index,
                'input': input_data,
                'expected_output': expected_output,
                'actual_output': actual_output,
                'status': 'PASS' if actual_output == expected_output else 'FAIL'
            }

            code_result['test_results'].append(test_result)

        results.append(code_result)

    return results
