#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot import issues with the LegalSupportCrew class.
This will print detailed information about the environment and module structure.
"""

import os
import sys
import glob
import json
import inspect
import importlib

# Save diagnostic results
results = {
    "environment": {},
    "directory_structure": {},
    "import_tests": [],
    "module_details": {}
}

# Environment information
results["environment"]["python_version"] = sys.version
results["environment"]["python_path"] = sys.executable
results["environment"]["path"] = sys.path
results["environment"]["cwd"] = os.getcwd()

# Directory structure
def scan_directory(path, max_depth=3, current_depth=0):
    if current_depth > max_depth:
        return ["[max depth reached]"]
    
    if not os.path.exists(path):
        return ["[directory does not exist]"]
    
    try:
        items = os.listdir(path)
        result = {}
        
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and current_depth < max_depth:
                result[item + "/"] = scan_directory(item_path, max_depth, current_depth + 1)
            else:
                result[item] = os.path.getsize(item_path) if os.path.isfile(item_path) else "[dir]"
        
        return result
    except Exception as e:
        return [f"[error: {str(e)}]"]

results["directory_structure"]["root"] = scan_directory(".")
results["directory_structure"]["src"] = scan_directory("./src", max_depth=4) if os.path.exists("./src") else "Not found"

# Import tests
def test_import(import_statement, description):
    test_result = {
        "description": description,
        "import_statement": import_statement,
        "success": False,
        "error": None,
        "module_attributes": None
    }
    
    try:
        exec(import_statement)
        test_result["success"] = True
        
        # Try to get the imported module/class attributes
        try:
            # Extract module name from import statement
            if " as " in import_statement:
                var_name = import_statement.split(" as ")[-1].strip()
            elif "from " in import_statement and " import " in import_statement:
                var_name = import_statement.split(" import ")[-1].strip()
            else:
                var_name = import_statement.split("import ")[-1].strip()
            
            # Get attributes
            obj = eval(var_name)
            if inspect.ismodule(obj):
                test_result["module_attributes"] = dir(obj)
            elif inspect.isclass(obj):
                test_result["module_attributes"] = [
                    attr for attr in dir(obj) 
                    if not attr.startswith("__") or not attr.endswith("__")
                ]
        except Exception as attr_error:
            test_result["module_attribute_error"] = str(attr_error)
    
    except Exception as e:
        test_result["error"] = str(e)
    
    results["import_tests"].append(test_result)
    return test_result["success"]

# Run various import tests
test_import("import sys", "Basic system import test")
test_import("import os", "Basic os import test")

# Test standard import
test_import(
    "from agents.crews.legal_support_agents.legal_support_agents import LegalSupportCrew", 
    "Standard import path"
)

# Test if module exists in root
if os.path.exists("legal_support_agents_module.py"):
    test_import(
        "from legal_support_agents_module import LegalSupportCrew", 
        "Import from copied module in root"
    )
else:
    results["import_tests"].append({
        "description": "Import from copied module in root",
        "import_statement": "from legal_support_agents_module import LegalSupportCrew",
        "success": False,
        "error": "File legal_support_agents_module.py does not exist in root directory"
    })

# Find any potential legal_support_agents.py files
legal_crew_files = glob.glob("src/**/legal_support_agents.py", recursive=True)
results["module_details"]["found_files"] = legal_crew_files

for i, file_path in enumerate(legal_crew_files):
    # Check if file contains LegalSupportCrew class
    try:
        with open(file_path, "r") as f:
            content = f.read()
            has_class = "class LegalSupportCrew" in content
            module_name = f"legal_support_agents_{i}"
            dir_name = os.path.dirname(file_path)
            
            results["module_details"][file_path] = {
                "has_class_definition": has_class,
                "size": os.path.getsize(file_path),
                "directory": dir_name,
                "dir_contents": os.listdir(dir_name) if os.path.exists(dir_name) else "N/A"
            }
            
            # Try to dynamically import
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    results["module_details"][file_path]["dynamic_import"] = "success"
                    results["module_details"][file_path]["module_dir"] = dir(module)
                    
                    if hasattr(module, "LegalSupportCrew"):
                        results["module_details"][file_path]["has_LegalSupportCrew"] = True
                    else:
                        results["module_details"][file_path]["has_LegalSupportCrew"] = False
                else:
                    results["module_details"][file_path]["dynamic_import"] = "failed to get spec"
            except Exception as e:
                results["module_details"][file_path]["dynamic_import"] = f"error: {str(e)}"
    except Exception as e:
        results["module_details"][file_path] = f"Error reading file: {str(e)}"

# Output the results
print(json.dumps(results, indent=2))

# Create a file with the results for easier access in Kudu console
with open("diagnostic_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nDiagnostic complete! Results saved to diagnostic_results.json") 