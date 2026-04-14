from flask import Flask, request
import requests
from datetime import datetime
import os

app = Flask(__name__)

VERIFY_TOKEN = "carla123"
ACCESS_TOKEN = "EAAWpLJ0IMf4BRKtqe7ZATwNIv1D4CGSCFIxcD1iiSlTRjyiHZB6AWRJkRZB6y1eEkSslDW8XMv8VsEZA1EaRCuKz9YugCmbgkxD5FLE1NAGFbmhWkhdbdDqLM6vPBeTPedyxZAudyuSnZBlKluSZBAZAZC8xOQ0FdeNrXYLoT0EcuUNZA1SDK4sbtVeLNNAV3diZBTp2tY68d6rtvjkWgF5zRwlyYY9jgKLlkENtmdddswIMKjM3oJlFybOPPYCSRYvroOT0zrViQyipqnzAm9ZCztsFQX8NowZDZD"
PHONE_NUMBER_ID = "1038275629374379"

usuarios = {}


@app.route("/", methods=["GET"])
def home():
    return "Bot Rocca rodando 🚀", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print("\n🔎 GET recebido no webhook", flush=True)
        print("mode:", mode, flush=True)
        print("token:", token, flush=True)
        print("challenge:", challenge, flush=True)

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro", 403

    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            print("\n📥 DADOS RECEBIDOS:", flush=True)
            print(data, flush=True)

            if not data:
                print("⚠️ Nenhum JSON recebido.", flush=True)
                return "ok", 200

            entry = data.get("entry", [])
            if not entry:
                print("⚠️ Sem 'entry' no payload.", flush=True)
                return "ok", 200

            changes = entry[0].get("changes", [])
            if not changes:
                print("⚠️ Sem 'changes' no payload.", flush=True)
                return "ok", 200

            value = changes[0].get("value", {})

            if "messages" in value:
                mensagem = value["messages"][0]
                numero = mensagem.get("from", "")
                texto = mensagem.get("text", {}).get("body", "").strip()

                print("\n📩 Mensagem recebida de:", numero, flush=True)
                print("Texto:", texto, flush=True)

                if not texto:
                    print("⚠️ Mensagem sem texto.", flush=True)
                    return "ok", 200

                resposta = processar_mensagem(numero, texto)

                print("\n🤖 RESPOSTA DO BOT:", flush=True)
                print(resposta, flush=True)

                enviar_mensagem(numero, resposta)

            elif "statuses" in value:
                print("\n📊 Status da Meta:", flush=True)
                print(value["statuses"], flush=True)

            else:
                print("⚠️ Evento sem messages e sem statuses.", flush=True)

        except Exception as e:
            print("\n❌ ERRO REAL:", repr(e), flush=True)

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

        print("\n🔥 NOVO ATENDIMENTO FINANCEIRO", flush=True)
        print(usuarios[numero], flush=True)

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

        print("\n🔧 NOVO CHAMADO DE MANUTENÇÃO", flush=True)
        print(usuarios[numero], flush=True)

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

        print("\n🏡 NOVO LEAD DE COMPRA", flush=True)
        print(usuarios[numero], flush=True)

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

        print("\n🏠 NOVO LEAD DE LOCAÇÃO", flush=True)
        print(usuarios[numero], flush=True)

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

        print("\n💰 NOVO LEAD INVESTIDOR", flush=True)
        print(usuarios[numero], flush=True)

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

        print("\n📞 SOLICITAÇÃO DE CORRETOR", flush=True)
        print(usuarios[numero], flush=True)

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

    token_prefix = ACCESS_TOKEN[:25] if ACCESS_TOKEN else "TOKEN_VAZIO"
    print("TOKEN PREFIXO:", token_prefix, flush=True)
    print("TOKEN TAMANHO:", len(ACCESS_TOKEN) if ACCESS_TOKEN else 0, flush=True)
    print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID, flush=True)
    print("NUMERO DESTINO:", numero, flush=True)

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

    print("\n📤 STATUS ENVIO:", resposta.status_code, flush=True)
    print("RESPOSTA META:", resposta.text, flush=True)

    resposta = requests.post(url, headers=headers, json=payload)
    print("\n📤 STATUS ENVIO:", resposta.status_code, flush=True)
    print("RESPOSTA META:", resposta.text, flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)