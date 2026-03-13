class SurveyQuestions:
    question1 = (
        """😊 *%s*,\n\n"""
        """Quero saber como foi sua experiência comigo aqui no WhatsApp.\n\n"""
        """É só digitar um número de 1 a 5.\n\n"""
        """Quanto maior a nota, melhor foi meu desempenho, ok? 😉\n"""
        """ \n"""
        """👎 1️⃣2️⃣3️⃣4️⃣5️⃣👍\n"""
    )
    question2 = (
        """Tenho outras 6 perguntinhas, que você pode responder\n"""
        """ com números de 1️⃣ a 5️⃣. Vamos começar?\n\n"""
        """1️⃣ Quero responder agora🤝\n"""
        """2️⃣ Prefiro outra hora ❌"""
    )
    question3 = (
        """✅–⬜–⬜–⬜–⬜–⬜ \n\n"""
        """O que você achou da variedade de produtos aqui no meu WhatsApp?\n"""
        """Encontrou o que desejava?\n\n"""
        """Digite uma nota de 1 a 5:\n\n"""
        """👎 1️⃣2️⃣3️⃣4️⃣5️⃣👍\n"""
    )
    question4 = (
        """✅–✅–⬜–⬜–⬜–⬜ \n\n"""
        """E como foi sua experiência de compra comigo?\n"""
        """Consegui entender direitinho o que você queria?\n\n"""
        """Digite uma nota de 1 a 5:\n\n"""
        """👎1️⃣2️⃣3️⃣4️⃣5️⃣👍\n"""
    )
    question5 = (
        """✅–✅–✅–⬜–⬜–⬜\n\n"""
        """Agora, me conta sobre a entrega.\n"""
        """Achou seu endereço e o melhor modo de envio com facilidade?\n\n"""
        """Digite uma nota de 1 a 5:\n\n"""
        """👎1️⃣2️⃣3️⃣4️⃣5️⃣👍\n"""
    )
    question6 = (
        """✅–✅–✅–✅–⬜–⬜\n\n"""
        """Sobre a finalização do pedido, foi fácil escolher o método\n"""
        """de pagamento e concluir a compra?\n\n"""
        """Digite uma nota de 1 a 5:\n\n"""
        """👎1️⃣2️⃣3️⃣4️⃣5️⃣👍\n"""
    )
    question7 = (
        """✅–✅–✅–✅–✅–⬜\n\n"""
        """Você conversou com o nosso atendente?\n"""
        """Se sim, pode me dizer como foi o atendimento?\n\n"""
        """Digite uma nota de 1 a 5:\n"""
        """👎1️⃣2️⃣3️⃣4️⃣5️⃣👍\n\n"""
        """Agora, se você não precisou de atendimento, é só clicar 0️⃣."""
    )
    question8 = (
        """✅–✅–✅–✅–✅–✅\n\n"""
        """E aí, já comprou pelo WhatsApp de outras marcas?\n\n"""
        """Se sim, pode me dizer *qual* foi?\n"""
        """É só digitar o nome da marca aqui embaixo ou 0️⃣,"""
        """se nunca comprou pelo WhatsApp 👇"""
    )
    acknowledgment_message = (
        """Aê, muito obrigada por participar! 🥰\n\n"""
        """Já guardei aqui suas notas e vou usá-las para """
        """que os próximos atendimentos aos nossos HavaLovers sejam melhores a cada dia.\n\n"""
        """Te espero para a próxima compra! Até lá 👋"""
    )
    sad_message = (
        """Poxa, sinto muito por isso. 😔\n"""
        """Pode me contar o que aconteceu ou o motivo da sua nota,\n"""
        """para eu entender melhor o seu caso?\n"""
        """É só digitar aqui embaixo 👇"""
    )
    sad_acknowledgment_message = (
        """Recebi sua resposta! 🙂\n"""
        """Se ainda precisar de ajuda, fale com a gente\n"""
        """pela Central de Relacionamento com o Consumidor:\n"""
        """(11) 3003-3414 (Grande São Paulo) ou 0800 70 70 566 (Demais Regiões).\n"""
        """Nossa equipe estará pronta para te ajudar, ok? 😉\n"""
        """Até a próxima 👋"""
    )
    give_up = (
        """Sem problemas! Então, daqui a alguns dias\n"""
        """ eu te pergunto novamente, combinado? 😉 \n"""
        """Até a próxima 👋"""
    )

    def __init__(self):
        pass

    @classmethod
    def get(self, idx, *args):
        return getattr(self, "question{}".format(idx))

    @classmethod
    def giveup(self):
        return self.give_up

    @classmethod
    def acknowledgment(self):
        return self.acknowledgment_message

    @classmethod
    def sad(self):
        return self.sad_message

    @classmethod
    def sad_acknowledgment(self):
        return self.sad_acknowledgment_message
