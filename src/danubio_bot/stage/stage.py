bot = {
    "stages": {
        "ask_start_menu": {
            "load_values": ["name"],
            "conditions": [
                {
                    "condition": "not {name}",
                    "true": {
                        "replies": [
                            {
                                "type": "text",
                                "text": "*Olá, seja bem-vindo ao Atendimento online da Atual Sistemas!!! Para iniciarmos, digite seu nome.*",
                            }
                        ],
                        "next_stage": "receive_name_stage",
                        "return": True,
                    },
                    "false": None,
                },
                {
                    "condition": None,
                    "replies": [
                        {
                            "type": "text",
                            "text": "{name}, qual o nome da empresa que deseja atendimento ?",
                        }
                    ],
                    "next_stage": "receive_company_name",
                    "return": None,
                },
            ],
        },
        "receive_name_stage": {
            "load_values": [],
            "conditions": [
                {
                    "condition": None,
                    "true": {
                        "replies": [
                            {
                                "type": "button",
                                "body": "Certo, então vou te chamar de '*{text}.split()[0].title()*', confirma?",
                                "buttons": [
                                    "Sim, Confirma!",
                                    "Não, quero corrigir!",
                                ],
                            }
                        ],
                        "next_stage": "receive_name_stage",
                        "return": True,
                    },
                    "false": None,
                },
                {
                    "condition": None,
                    "replies": [
                        {
                            "type": "text",
                            "text": "{name}, qual o nome da empresa que deseja atendimento ?",
                        }
                    ],
                    "next_stage": "receive_company_name",
                    "return": True,
                },
            ],
        },
        "receive_company_name": {
            "load_values": ["name"],
            "conditions": [
                {
                    "condition": "not {name}",
                    "true": {
                        "replies": [
                            {
                                "type": "text",
                                "text": "*Olá, seja bem-vindo ao Atendimento online da Atual Sistemas!!! Para iniciarmos, digite seu nome.*",
                            }
                        ],
                        "next_stage": "receive_name_stage",
                        "return": True,
                    },
                    "false": None,
                },
                {
                    "condition": None,
                    "replies": [
                        {
                            "type": "text",
                            "text": "{name}, qual o nome da empresa que deseja atendimento ?",
                        }
                    ],
                    "next_stage": "receive_company_name",
                    "return": True,
                },
            ],
        },
    }
}
