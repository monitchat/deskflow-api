#!/usr/bin/env python3
"""
Script para adicionar o check de execute_children no início dos executors de processamento.
"""

import re

# Lê o arquivo
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'r') as f:
    lines = f.readlines()

# Nós que precisam do check
nodes_needing_check = [
    '_execute_api_call_node',
    '_execute_api_request_node',
    '_execute_set_context_node',
    '_execute_transfer_node',
    '_execute_end_node',
]

def add_execute_children_check(lines):
    i = 0
    result = []

    while i < len(lines):
        line = lines[i]

        # Detecta definição de função que precisa do check
        for node_name in nodes_needing_check:
            if re.match(rf'\s+def {node_name}\(self, node, msisdn, text, execute_children=True\):', line):
                result.append(line)
                i += 1

                # Adiciona docstring se houver
                if i < len(lines) and '"""' in lines[i]:
                    result.append(lines[i])
                    i += 1
                    # Continua até o fim da docstring
                    while i < len(lines) and '"""' not in lines[i]:
                        result.append(lines[i])
                        i += 1
                    if i < len(lines):
                        result.append(lines[i])
                        i += 1

                # Procura pela primeira linha de código real (não comentário)
                while i < len(lines) and (lines[i].strip().startswith('#') or not lines[i].strip()):
                    result.append(lines[i])
                    i += 1

                # Verifica se já tem o check de execute_children
                if i < len(lines) and 'if not execute_children:' not in lines[i]:
                    # Adiciona o check
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    spaces = ' ' * indent
                    result.append(f'{spaces}# Se não deve executar filhos, retorna vazio\n')
                    result.append(f'{spaces}if not execute_children:\n')
                    result.append(f'{spaces}    return []\n')
                    result.append('\n')

                continue

        result.append(line)
        i += 1

    return result

# Processa o arquivo
new_lines = add_execute_children_check(lines)

# Escreve de volta
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Execute_children checks added successfully!")
print(f"Total lines: {len(new_lines)}")
