from flask import Flask, request
import requests
from datetime import datetime
import os

app = Flask(__name__)

VERIFY_TOKEN = "carla123"
ACCESS_TOKEN = "EAAWpLJ0IMf4BRIQvuRH6ZCcFxrxOdbLbWjKQZBFiN1zf4DOR9ylZBXsG4TmMXtuoGYLelsUtvcNF5rbZCwjs1EtIqdGffVSfSrLDKOZBK7goRwhgzd7YZCwxoIifev6aPa6XWSuZCBFytSswPXfrimXsNEx8yVwcA6dD1b2p1qDDETZADyahPKMVZAC6QjG6ZCym7bUHCurbUEERLlDRV1n4bUMKkoMxwq95oEisGT6w2Tb7vy82uuNK0YMgAQ8FZBRZC1tEps2EoocjNCnpAAr9s4vofSSG"
PHONE_NUMBER_ID = "1038275629374379"

usuarios = {}


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro", 403

    if request.method == "POST":
        data = request.get_json()
        print("\n📥 DADOS RECEBIDOS:")
        print(data)

        try:
            value = data["entry"][0]["changes"][0]["value"]

            if "messages" in value:
                mensagem = value["messages"][0]
                numero = mensagem["from"]
                texto = mensagem.get("text", {}).get("body", "").strip()

                print("\n📩 Mensagem recebida de:", numero)
                print("Texto:", texto)

                resposta = processar_mensagem(numero, texto)

                print("\n🤖 RESPOSTA DO BOT:")
                print(resposta)

                enviar_mensagem(numero, resposta)

            elif "statuses" in value:
                print("\n📊 Status da Meta:")
                print(value["statuses"])

        except Exception as e:
            print("\n❌ Erro ao processar webhook:", e)

        return "ok", 200


def processar_mensagem(numero, texto):
    texto = texto.strip().lower()

    if texto == "reiniciar":
        usuarios[numero] = {"etapa": "inicio"}
        return "🔄 Vamos começar novamente 😊"

    if numero not in usuarios:
        usuarios[numero] = {"etapa": "inicio"}

    etapa = usuarios[numero]["etapa"]

    if etapa == "inicio":
        usuarios[numero]["etapa"] = "tipo_cliente"
        return (
            "Olá! Seja bem-vindo à *Rocca Imóveis* 😊\n\n"
            "Você já é cliente da Rocca?\n"
            "1 - Sim\n"
            "2 - Não"
        )

    if etapa == "tipo_cliente":
        if texto == "1":
            usuarios[numero]["etapa"] = "cliente_opcao"
            return (
                "Perfeito!\n"
                "Como podemos te ajudar?\n\n"
                "1 - Financeiro\n"
                "2 - Manutenção/Desocupação"
            )

        elif texto == "2":
            usuarios[numero]["etapa"] = "nao_cliente_opcao"
            return (
                "Perfeito! 😊\n"
                "Como podemos te ajudar?\n\n"
                "1 - Comprar imóvel\n"
                "2 - Alugar imóvel\n"
                "3 - Investir\n"
                "4 - Falar com corretor"
            )

        return "Digite 1 para SIM ou 2 para NÃO."

    if etapa == "cliente_opcao":
        if texto == "1":
            usuarios[numero]["tipo"] = "Financeiro"
            usuarios[numero]["etapa"] = "financeiro_nome"
            return "Certo! Qual seu nome completo?"

        elif texto == "2":
            usuarios[numero]["tipo"] = "Manutenção"
            usuarios[numero]["etapa"] = "manutencao_imovel"
            return "Qual o imóvel/unidade?"

        return "Escolha 1 ou 2."

    if etapa == "financeiro_nome":
        usuarios[numero]["nome"] = texto
        usuarios[numero]["etapa"] = "financeiro_assunto"
        return "Qual o assunto?"

    if etapa == "financeiro_assunto":
        usuarios[numero]["assunto"] = texto

        print("\n🔥 NOVO ATENDIMENTO FINANCEIRO")
        print(usuarios[numero])

        salvar_atendimento("Financeiro", {
            "telefone": numero,
            "nome": usuarios[numero].get("nome", ""),
            "assunto": usuarios[numero].get("assunto", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Perfeito! Nosso time financeiro irá te atender em breve."

    if etapa == "manutencao_imovel":
        usuarios[numero]["imovel"] = texto
        usuarios[numero]["etapa"] = "manutencao_problema"
        return "Qual o problema ou solicitação?"

    if etapa == "manutencao_problema":
        usuarios[numero]["problema"] = texto

        print("\n🔧 NOVO CHAMADO DE MANUTENÇÃO")
        print(usuarios[numero])

        salvar_atendimento("Manutenção/Desocupação", {
            "telefone": numero,
            "imovel": usuarios[numero].get("imovel", ""),
            "problema": usuarios[numero].get("problema", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Solicitação registrada! Em breve entraremos em contato."

    if etapa == "nao_cliente_opcao":
        opcoes = {
            "1": "Comprar",
            "2": "Alugar",
            "3": "Investir",
            "4": "Corretor"
        }

        if texto not in opcoes:
            return "Escolha uma opção válida (1 a 4)."

        usuarios[numero]["tipo"] = opcoes[texto]

        if texto == "1":
            usuarios[numero]["etapa"] = "comprar_local"
            return "Em qual cidade ou bairro você procura?"

        if texto == "2":
            usuarios[numero]["etapa"] = "alugar_local"
            return "Em qual cidade ou bairro você procura?"

        if texto == "3":
            usuarios[numero]["etapa"] = "investir_valor"
            return "Qual faixa de valor pretende investir?"

        if texto == "4":
            usuarios[numero]["etapa"] = "corretor_nome"
            return "Qual seu nome?"

    if etapa == "comprar_local":
        usuarios[numero]["local"] = texto
        usuarios[numero]["etapa"] = "comprar_valor"
        return "Qual faixa de valor?"

    if etapa == "comprar_valor":
        usuarios[numero]["valor"] = texto
        usuarios[numero]["etapa"] = "comprar_tipo"
        return "Qual tipo de imóvel?"

    if etapa == "comprar_tipo":
        usuarios[numero]["tipo_imovel"] = texto
        usuarios[numero]["etapa"] = "comprar_financiamento"
        return "Pretende financiar? (sim/não)"

    if etapa == "comprar_financiamento":
        usuarios[numero]["financiamento"] = texto

        print("\n🏡 NOVO LEAD DE COMPRA")
        print(usuarios[numero])

        salvar_atendimento("Compra", {
            "telefone": numero,
            "local": usuarios[numero].get("local", ""),
            "valor": usuarios[numero].get("valor", ""),
            "tipo_imovel": usuarios[numero].get("tipo_imovel", ""),
            "financiamento": usuarios[numero].get("financiamento", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Perfeito! Um corretor entrará em contato."

    if etapa == "alugar_local":
        usuarios[numero]["local"] = texto
        usuarios[numero]["etapa"] = "alugar_valor"
        return "Qual valor mensal?"

    if etapa == "alugar_valor":
        usuarios[numero]["valor"] = texto
        usuarios[numero]["etapa"] = "alugar_tipo"
        return "Qual tipo de imóvel?"

    if etapa == "alugar_tipo":
        usuarios[numero]["tipo_imovel"] = texto

        print("\n🏠 NOVO LEAD DE LOCAÇÃO")
        print(usuarios[numero])

        salvar_atendimento("Locação", {
            "telefone": numero,
            "local": usuarios[numero].get("local", ""),
            "valor": usuarios[numero].get("valor", ""),
            "tipo_imovel": usuarios[numero].get("tipo_imovel", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Perfeito! Vamos te enviar opções."

    if etapa == "investir_valor":
        usuarios[numero]["valor"] = texto
        usuarios[numero]["etapa"] = "investir_objetivo"
        return "Busca renda mensal ou valorização?"

    if etapa == "investir_objetivo":
        usuarios[numero]["objetivo"] = texto

        print("\n💰 NOVO LEAD INVESTIDOR")
        print(usuarios[numero])

        salvar_atendimento("Investidor", {
            "telefone": numero,
            "valor": usuarios[numero].get("valor", ""),
            "objetivo": usuarios[numero].get("objetivo", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Perfeito! Um especialista entrará em contato."

    if etapa == "corretor_nome":
        usuarios[numero]["nome"] = texto
        usuarios[numero]["etapa"] = "corretor_assunto"
        return "Qual o assunto?"

    if etapa == "corretor_assunto":
        usuarios[numero]["assunto"] = texto

        print("\n📞 SOLICITAÇÃO DE CORRETOR")
        print(usuarios[numero])

        salvar_atendimento("Falar com corretor", {
            "telefone": numero,
            "nome": usuarios[numero].get("nome", ""),
            "assunto": usuarios[numero].get("assunto", "")
        })

        usuarios[numero]["etapa"] = "finalizado"
        return "Perfeito! Um corretor vai te chamar."

    if etapa == "finalizado":
        return "Se quiser recomeçar, digite: reiniciar"

    return "Não entendi, pode repetir?"


def salvar_atendimento(tipo, dados):
    with open("atendimentos.txt", "a", encoding="utf-8") as arquivo:
        arquivo.write("\n" + "=" * 50 + "\n")
        arquivo.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        arquivo.write(f"Tipo de atendimento: {tipo}\n")

        for chave, valor in dados.items():
            arquivo.write(f"{chave}: {valor}\n")


def enviar_mensagem(numero, texto):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    resposta = requests.post(url, headers=headers, json=payload)
    print("\n📤 STATUS ENVIO:", resposta.status_code)
    print("RESPOSTA META:", resposta.text)


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)