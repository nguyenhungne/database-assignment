import re
from itertools import combinations

# Exercise 1
def extract_info(line):
    # Regex to extract table name, attributes, primary key, and relationship
    pattern_table_name = r"\[([A-Za-z\s]+)\]"
    pattern_attributes = r"\(([^)]+)\)"
    pattern_pk = r"([A-Za-z0-9\s]+: PK)"
    pattern_relationship = r"(\d+\s?–\s?\d+|\w+\s?–\s?\w+)"
    
    # Table 1
    table_1 = re.search(pattern_table_name, line)
    attributes_1 = re.search(pattern_attributes, line)
    pk_1 = re.search(pattern_pk, line)
    
    start_slice = pk_1.end() if pk_1 else (attributes_1.end() if attributes_1 else table_1.end())
    # Table 2
    table_2_start = line[start_slice:] if table_1 else line
    table_2 = re.search(pattern_table_name, table_2_start)
    attributes_2 = re.search(pattern_attributes, table_2_start)
    pk_2 = re.search(pattern_pk, table_2_start)
    
    # Relationship
    relationship = re.search(pattern_relationship, line)
    
    # Extracted information
    info = {
        "table_1": table_1.group(1) if table_1 else None,
        "attributes_1": attributes_1.group(1) if attributes_1 else None,
        "pk_1": pk_1.group(1).split(":")[0] if pk_1 else None,
        "table_2": table_2.group(1) if table_2 else None,
        "attributes_2": attributes_2.group(1) if attributes_2 else None,
        "pk_2": pk_2.group(1).split(":")[0] if pk_2 else None,
        "relationship": relationship.group(1) if relationship else None
    }
    
    return info

def build_table_from_data(data, is_nhieu_nhieu=False):
    table_1 = data['table_1']
    attributes_1 = data['attributes_1'].split(', ')
    pk_1 = data['pk_1']
    
    table_2 = data['table_2']
    attributes_2 = data['attributes_2'].split(', ')
    pk_2 = data['pk_2']
    
    relationship = data['relationship']
    
    table_1_str = f"[{table_1}] ({', '.join(attributes_1)})"
    table_2_str = f"[{table_2}] ({', '.join(attributes_2)})"

    if pk_1:
        table_1_str += f" ({pk_1}: PK)"
    if pk_2:
        table_2_str += f" ({pk_2}: PK)"
    
    if is_nhieu_nhieu:
        intermediate_table_str = f"[{table_1}_{table_2}] ({pk_1}, {pk_2}: PK)"

        result = f"{table_1_str} – {intermediate_table_str} – {table_2_str}: {relationship}"

        return result
    
    result = f"{table_1_str} – {table_2_str}: {relationship}"
    return result

# Hàm convert_erd_to_relational tích hợp với extract_info
def convert_erd_to_relational(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        info = extract_info(line)
        
        relationship = info['relationship']
        if relationship == '1 – n':
            new_info = {
                **info,
                "attributes_2": f"{info['attributes_2']}, {info['pk_1']}"
            }
            output_lines.append(build_table_from_data(new_info))
        elif relationship == 'n – 1':
            new_info = {
                **info,
                "attributes_1": f"{info['attributes_1']}, {info['pk_2']}"
            }
            output_lines.append(build_table_from_data(new_info))
        elif relationship == 'Cha – con':
            new_info
            if info['pk_2']:
                new_info = {
                    **info,
                    "attributes_2": f"{info['pk_2']}, {info['attributes_1']}"
                }
            else:
                new_info = {
                    **info,
                    "attributes_2": f"{info['attributes_1'].split(', ')[0]}, {info['attributes_2']}"
                }
            output_lines.append(build_table_from_data(new_info))
        elif relationship == 'Con – cha':
            new_info
            if info['pk_1']:
                new_info = {
                    **info,
                    "attributes_1": f"{info['pk_1']}, {info['attributes_2']}"
                }
            else:
                new_info = {
                    **info,
                    "attributes_1": f"{info['attributes_2'].split(', ')[0]}, {info['attributes_1']}"
                }
            output_lines.append(build_table_from_data(new_info))

        elif relationship == 'n – n':
            output_lines.append(build_table_from_data(info, is_nhieu_nhieu=True))
        else:
            output_lines.append(build_table_from_data(info))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))


# Exercise 2
def read_input(file_path):
    tables = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
        current_table = None
        current_deps = []
        for line in lines:
            line = line.strip()
            if line.startswith('Table'):
                if current_table:
                    tables.append((current_table, current_deps))
                table_name, attributes = line.split(':')
                table_name = table_name.split()[1]
                attributes = attributes.strip()[1:-1].split(', ')
                current_table = {
                    'table_name': table_name,
                    'attributes': attributes
                }
                current_deps = []
            elif line.startswith('Functional dependencies'):
                continue
            elif '->' in line:
                current_deps.append(line)
        if current_table:
            tables.append((current_table, current_deps))
    
    return tables

def write_output(file_path, table_name, minimal_keys):
    with open(file_path, 'a') as f:
        f.write(f"Keys for Table {table_name}:\n")
        for key in minimal_keys:
            f.write(', '.join(sorted(key)) + '\n')
        f.write('\n')

def compute_closure(attributes, fds):
    closure = set(attributes)
    while True:
        new_closure = closure.copy()
        for left, right in fds:
            if set(left).issubset(closure):
                new_closure.update(right)
        if new_closure == closure:
            break
        closure = new_closure
    return closure

def determine_candidate_keys(relation, fds):
    # Step 1: Attributes neither on the left nor the right of any FD
    left_attributes = set(attr for fd in fds for attr in fd[0])
    right_attributes = set(attr for fd in fds for attr in fd[1])
    neither_attributes = set(relation) - left_attributes - right_attributes

    # Step 2: Attributes only on the left side
    only_left_attributes = left_attributes - right_attributes

    # Step 3: Attributes only on the right side
    only_right_attributes = right_attributes - left_attributes

    # Step 4: Combine Step 1 and Step 2 attributes
    combined_attributes = neither_attributes | only_left_attributes

    # Step 5: Compute closure of combined attributes
    closure_of_combined = compute_closure(combined_attributes, fds)
    if set(relation) == closure_of_combined:
        return [combined_attributes]  # It's the only candidate key

    # Step 6: Attributes not in Step 3 or Step 4
    remaining_attributes = set(relation) - only_right_attributes - combined_attributes

    # Step 7: Compute minimal closures equal to R
    candidate_keys = []
    for size in range(1, len(remaining_attributes) + 1):
        for subset in combinations(remaining_attributes, size):
            closure = compute_closure(combined_attributes | set(subset), fds)
            if set(relation) == closure:
                # Check minimality
                if not any(set(candidate).issubset(set(subset)) for candidate in candidate_keys):
                    candidate_keys.append(set(subset))

    return candidate_keys

def convert_fds(fds_string):
    fds = []
    for fd in fds_string:
        left, right = fd.split(' -> ')
        
        left_attributes = left.split(', ')
        right_attributes = right.split(', ')
        
        fds.append((left_attributes, right_attributes))
    return fds
   
if __name__ == "__main__":
    # Exercise 1
    input_file = "Input1.txt"
    output_file = "Output1.txt"
    convert_erd_to_relational(input_file, output_file)

    # Exercise 2
    tables = read_input('Input2.txt')
    for table, fds_string in tables:
        fds = convert_fds(fds_string)
        candidate_keys = determine_candidate_keys(table['attributes'], fds)
        write_output('output2.txt', table['table_name'], candidate_keys)
