#!/usr/bin/env python3
"""
Script para aplicar a lógica de execute_children em todos os executors.
"""

import re

# Lê o arquivo
with open('/home/luiz-ricardo/projects/deskflow/src/deskflow/flow_interpreter.py', 'r') as f:
    lines = f.readlines()

# Linhas que precisam ser atualizadas (api_call, api_request, set_context, transfer, end)
# Elas estão nas linhas 608, 801, 856, 903

# Padrão a ser substituído:
# De:
#   for next_node_id in next_nodes:
#       replies = self.execute_node(next_node_id, msisdn, text)
#       all_replies.extend(replies)
#
# Para:
#   if len(next_nodes) > 1:
#       for next_node_id in next_nodes:
#           replies = self.execute_node(next_node_id, msisdn, text, execute_children=False)
#           all_replies.extend(replies)
#   elif len(next_nodes) == 1:
#       replies = self.execute_node(next_nodes[0], msisdn, text, execute_children=True)
#       all_replies.extend(replies)

def process_file(lines):
    i = 0
    result = []

    while i < len(lines):
        line = lines[i]

        # Detecta o padrão "for next_node_id in next_nodes:"
        if re.match(r'\s+for next_node_id in next_nodes:', line):
            indent = len(line) - len(line.lstrip())
            spaces = ' ' * indent

            # Verifica se as próximas 2 linhas seguem o padrão esperado
            if (i + 2 < len(lines) and
                'self.execute_node(next_node_id, msisdn, text)' in lines[i+1] and
                ('replies.extend' in lines[i+2] or 'all_replies.extend' in lines[i+2])):

                # Verifica se já está usando execute_children (se sim, pula)
                if 'execute_children=' in lines[i+1]:
                    result.append(line)
                    i += 1
                    continue

                # Extrai o nome da variável de replies
                replies_var = 'all_replies' if 'all_replies' in lines[i+2] else 'replies'

                # Substitui pelo novo padrão
                result.append(f'{spaces}# Se há múltiplos próximos nós (sem condição), executa todos mas SEM seus filhos\n')
                result.append(f'{spaces}if len(next_nodes) > 1:\n')
                result.append(f'{spaces}    for next_node_id in next_nodes:\n')
                result.append(f'{spaces}        replies = self.execute_node(next_node_id, msisdn, text, execute_children=False)\n')
                result.append(f'{spaces}        {replies_var}.extend(replies)\n')
                result.append(f'{spaces}# Se há apenas 1 próximo nó, executa normalmente (COM seus filhos)\n')
                result.append(f'{spaces}elif len(next_nodes) == 1:\n')
                result.append(f'{spaces}    replies = self.execute_node(next_nodes[0], msisdn, text, execute_children=True)\n')
                result.append(f'{spaces}    {replies_var}.extend(replies)\n')

                # Pula as 3 linhas originais
                i += 3
                continue

        result.append(line)
        i += 1

    return result

# Processa o arquivo
new_lines = process_file(lines)

# Escreve de volta
with open('/home/luiz-ricardo/projects/deskflow/src/deskflow/flow_interpreter.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Execute_children logic applied successfully!")
print(f"Total lines: {len(new_lines)}")
