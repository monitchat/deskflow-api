#!/usr/bin/env python3
"""
Script para corrigir a propagação de text nos nós de processamento.
Nós de processamento devem passar text="" para os filhos.
"""

import re

# Lê o arquivo
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'r') as f:
    content = f.read()

# Padrões para substituir nos nós de processamento (input, api_call, api_request, set_context, transfer, end)
# Substitui: self.execute_node(next_node_id, msisdn, text, ...
# Por:       self.execute_node(next_node_id, msisdn, text="", ...

# Pattern 1: self.execute_node(next_node_id, msisdn, text, execute_children=False)
content = re.sub(
    r'self\.execute_node\(next_node_id, msisdn, text, execute_children=False\)',
    r'self.execute_node(next_node_id, msisdn, text="", execute_children=False)',
    content
)

# Pattern 2: self.execute_node(next_nodes[0], msisdn, text, execute_children=True)
content = re.sub(
    r'self\.execute_node\(next_nodes\[0\], msisdn, text, execute_children=True\)',
    r'self.execute_node(next_nodes[0], msisdn, text="", execute_children=True)',
    content
)

# Pattern 3: self.execute_node(next_node_id, msisdn, text)
content = re.sub(
    r'self\.execute_node\(next_node_id, msisdn, text\)(?!\,)',
    r'self.execute_node(next_node_id, msisdn, text="")',
    content
)

# Pattern 4: self.execute_node(next_nodes[0], msisdn, text)
content = re.sub(
    r'self\.execute_node\(next_nodes\[0\], msisdn, text\)(?!\,)',
    r'self.execute_node(next_nodes[0], msisdn, text="")',
    content
)

# Escreve de volta
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'w') as f:
    f.write(content)

print("✅ Text propagation fixed!")
