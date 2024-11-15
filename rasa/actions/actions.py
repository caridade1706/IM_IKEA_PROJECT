# from rasa_sdk import Action
# from rasa_sdk.executor import CollectingDispatcher
# from rasa_sdk.interfaces import Tracker

# class ActionShowProducts(Action):
#     def name(self):
#         return "action_show_products"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: dict):
#         category = tracker.get_slot("category")  # Supondo que "category" seja uma entidade
#         if category == "cadeiras":
#             dispatcher.utter_message(text="Aqui estão as cadeiras disponíveis...")
#         elif category == "mesas":
#             dispatcher.utter_message(text="Aqui estão as mesas disponíveis...")
#         else:
#             dispatcher.utter_message(text="Categoria não encontrada.")
#         return []

import http.client
import json
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker


class ActionShowProducts(Action):
    def name(self):
        return "action_show_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        # Obtém a categoria da entidade "category"
        category = tracker.get_slot("category")
        if not category:
            dispatcher.utter_message(text="Não consegui entender a categoria que você quer buscar.")
            return []

        try:
            # Conexão com a API do IKEA
            conn = http.client.HTTPSConnection("ikea-api.p.rapidapi.com")

            # Headers para autenticação
            headers = {
                'x-rapidapi-key': "f6ac7694f0mshad1a1e112b29308p1def65jsn84a5131e4970",
                'x-rapidapi-host': "ikea-api.p.rapidapi.com"
            }

            # Endpoint da API com o termo de busca
            endpoint = f"/keywordSearch?keyword={category}&countryCode=pt&languageCode=pt"

            # Faz a requisição à API
            conn.request("GET", endpoint, headers=headers)

            print(f"Requisição GET para {endpoint}")
            

            res = conn.getresponse()
            data = res.read()
            products = json.loads(data.decode("utf-8"))  # Decodifica a resposta JSON

            # Verifica se há produtos na resposta
            if not products:
                dispatcher.utter_message(text=f"Não encontrei produtos na categoria '{category}'.")
                return []

            # Prepara a lista de produtos
            product_list = "\n".join([
                f"- {item['name']} (Preço: {item['price']['currentPrice']} {item['price']['currency']})"
                for item in products[:5]  # Mostra os 5 primeiros produtos
            ])

            dispatcher.utter_message(
                text=f"Aqui estão alguns produtos da categoria '{category}':\n{product_list}"
            )

        except Exception as e:
            # Tratamento de erros
            dispatcher.utter_message(
                text="Desculpe, houve um problema ao buscar os produtos. Tente novamente mais tarde."
            )
            print(f"Erro na integração com a API do IKEA: {e}")

        return []
