#!/usr/bin/env python3
"""Script para adicionar execute_children parameter a todos os executors"""

import re

def add_execute_children_logic(content):
    """Adiciona a lógica de execute_children para todos os executors"""

    # Pattern para encontrar definições de executors
    executor_patterns = [
        (
            r'(    def _execute_button_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_list_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_condition_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_router_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_input_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_api_call_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_api_request_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_set_context_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_transfer_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
        (
            r'(    def _execute_end_node\(self, node, msisdn, text)\):',
            r'\1, execute_children=True):'
        ),
    ]

    for pattern, replacement in executor_patterns:
        content = re.sub(pattern, replacement, content)

    return content

# Ler o arquivo
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'r') as f:
    content = f.read()

# Aplicar as mudanças
content = add_execute_children_logic(content)

# Escrever de volta
with open('/home/luiz-ricardo/projects/bot-danubio/src/danubio_bot/flow_interpreter.py', 'w') as f:
    f.write(content)

print("✅ Signatures updated successfully!")
