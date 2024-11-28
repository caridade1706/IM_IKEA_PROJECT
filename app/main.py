import http.client
import json
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import unicodedata
import time

from os import system
import xml.etree.ElementTree as ET
import ssl
import websockets

from tts import TTS


not_quit = True
intent_before = ""
products_retrived = []


intents_list = ["ask_help", "show_products", "open_website", "scroll_up", "scroll_down", "select_product_by_position", "add_to_cart", "add_to_favorites", "show_cart", "show_favorites"]

driver = None

# Função para abrir o site (exemplo, IKEA) usando o Selenium
def open_website():
    """
    Função que usa o Selenium para abrir o site do IKEA e tentar clicar no botão de aceitação de cookies.
    """
    global driver
    website = "https://www.ikea.com/pt/pt/"  # URL do site para abrir

    try:
        # Verifica se o driver já está ativo ou precisa ser reiniciado
        if driver is None or not is_driver_alive():
            # Caminho do driver do Selenium (atualize conforme necessário)
            service = Service("C:\\Users\\Usuario\\Downloads\\chromedriver-win64\\chromedriver.exe")  # Atualize para o caminho correto
            driver = webdriver.Chrome(service=service)
        
        # Abre o site
        driver.get(website)
        driver.maximize_window()  # Maximiza a janela do navegador

        # Espera e tenta clicar no botão de aceitação de cookies
        try:
            wait = WebDriverWait(driver, 10)
            cookie_button = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
        except Exception:
            print("Não foi possível encontrar o botão de aceitação de cookies.")
        
        print(f"Abrindo o site do IKEA Portugal...")

    except Exception as e:
        print(f"Erro ao abrir o site: {str(e)}")

def remove_accents(input_str):
    if input_str is not None:
        # Transforma em formato Unicode Normalizado e remove caracteres acentuados
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return None

def show_product(category, tts):

    #remove acentos qualquer tipo de acento
    category2 = remove_accents(category)

    global driver

    if driver is None:
        print("Driver não foi inicializado.")
        return
      
    if not category:
        tts(text="Não consegui entender a categoria que gostaria de procurar.")
        return []

    try:
            
        print("A iniciar pedido:")
        tts(f"A procurar por {category} no site da IKEA Portugal")
            
        # Conexão com a API do IKEA
        conn = http.client.HTTPSConnection("ikea-api.p.rapidapi.com")
        # Headers para autenticação
        headers = {
            'x-rapidapi-key': "f6ac7694f0mshad1a1e112b29308p1def65jsn84a5131e4970",
            'x-rapidapi-host': "ikea-api.p.rapidapi.com"
        }

        # Endpoint da API com o termo de busca
        endpoint = f"/keywordSearch?keyword={category2}&countryCode=pt&languageCode=pt"

        # Faz a requisição à API
        conn.request("GET", endpoint, headers=headers)

        print(f"Requisição GET para {endpoint}")
        

        res = conn.getresponse()
        data = res.read()
        products = json.loads(data.decode("utf-8"))  # Decodifica a resposta JSON

        products_retrived.clear()
        
        for product in products:
                products_retrived.append(product)

            # Verifica se há produtos na resposta
        if not products:
            tts(f"Não encontrei produtos na categoria '{category}'.")
            return []

        # Prepara a lista de produtos
        product_list = "\n".join([
            f"- {item['name']} (Preço: {item['price']['currentPrice']} {item['price']['currency']})"
            for item in products[:5]  # Mostra os 5 primeiros produtos
        ])

        tts(f"Aqui estão alguns produtos da categoria '{category}':\n{product_list}")

    except Exception as e:
        # Tratamento de erros
        tts("Desculpe, houve um problema ao procurar os produtos. Tente novamente mais tarde.")
        print(f"Erro na integração com a API do IKEA: {e}")

    try:
        print("Buscando no site da IKEA com Selenium...")

        driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")

        time.sleep(2)

        # Localiza o campo de busca
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-field__input"))
            )            
        search_box.send_keys(Keys.CONTROL + "a")  # Seleciona todo o texto
        search_box.send_keys(Keys.BACKSPACE)  # Apaga o texto selecionado
        search_box.send_keys(category2)

        # Aciona o botão de busca
        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-box__searchbutton"))  # Ajuste conforme o ID correto
        )
        search_button.click()

    except Exception as e:
            tts("Houve um problema ao realizar a busca no site. Tente novamente mais tarde.")
            print(f"Erro no Selenium: {e}")

    return []


def is_driver_alive() -> bool:
    """
    Verifica se o driver do Selenium ainda está ativo.
    """
    try:
        driver.title  # Verifica se o driver ainda tem acesso à página
        return True
    except:
        close_driver()  # Fecha o driver se não estiver mais ativo
        return False

def close_driver():
    """
    Fecha o driver se ele estiver inicializado.
    """
    global driver
    if driver:
        try:
            driver.quit()  # Fecha o driver do Selenium
        except Exception:
            pass  # Ignora exceções durante o fechamento
        driver = None  # Define o driver como None após fechá-lo

def scroll_down():
    """
    Rola a página para baixo usando o Selenium.
    """
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Rola a página suavemente para baixo (500px)
        driver.execute_script("window.scrollBy({top: 500, behavior: 'smooth'});")  # Ajuste o valor conforme necessário
        print("A página foi rolada para baixo.")
    
    except Exception as e:
        print(f"Houve um problema ao rolar a página: {e}")

def scroll_up():
    """
    Rola a página para cima usando o Selenium.
    """
    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return

    try:
        # Rola a página suavemente para cima (500px)
        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")  # Ajuste o valor conforme necessário
        print("A página foi rolada para cima.")
    
    except Exception as e:
        print(f"Houve um problema ao rolar a página: {e}")

def select_product_by_positions(position, tts):

    global driver
    if driver is None:
        print("Driver não foi inicializado.")
        return
    
    #         # Verifica se a posição foi fornecida e é válida
#         if not position:
#             dispatcher.utter_message(text="Desculpe, não entendi a posição do produto que você quer.")
#             return []

#         try:
#             # Converte a posição para inteiro
#             position = int(position) - 1  # Subtrai 1 para ajustar ao índice da lista (começa em 0)
#             print(f"Selecionando produto na posição {position + 1}...")
#             driver = ActionOpenWebsite.driver
#             if not driver:
#                 dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
#                 return []

#             product_retrived = products_retrived[position]

#             driver.get(product_retrived['url'])

#             dispatcher.utter_message(
#                 text=f"O produto na posição {position + 1} foi selecionado."
#             )
#         except ValueError:
#             dispatcher.utter_message(
#                 text="Por favor, informe um número válido para a posição."
#             )
#         except Exception as e:
#             dispatcher.utter_message(
#                 text="Houve um problema ao selecionar o produto. Tente novamente mais tarde."
#             )
#             print(f"Erro ao selecionar produto: {e}")

#         return []
    
    
    



async def message_handler(message, tts):
    # Processa a mensagem e extrai o intent
    message = process_message(message)
    print(f"Message: {message}")
    
    if message == "OK":
        return "OK"
    
    intent = message["intent"]["name"]
    confidence = message["intent"]["confidence"]
    
    print(f"Intent: {intent} com confiança: {confidence}")
    
    # Verifica o intent e executa a ação correspondente
    if intent == "open_website":
        # Se o intent for "open_website", chama a função para abrir o site
        print("Abrindo o site...")
        tts("A abrir o site da IKEA PORTUGAL")
        open_website()

    elif intent == "show_products":
        # Aqui você pode adicionar lógica para mostrar produtos, etc.
        category = message['entities'][0]['value']
        print(f"Mostrando produtos de {category} ...")
        # Chame a função que exibe produtos aqui, por exemplo
        show_product(category, tts)

    elif intent == "scroll_down":
        # Se o intent for "scroll_up", chama a função para rolar para cima
        print("A descer a pagina")
        tts("A descer a página")
        scroll_down()

    elif intent == "scroll_up":
        # Se o intent for "scroll_up", chama a função para rolar para cima
        print("A subir a pagina")
        tts("A subir a página")
        scroll_up()

    elif intent == "select_product_by_position":
        position = message['entities'][0]['value']
        print(f"A selecionar o producto na posição {position}..")
        select_product_by_positions(position, tts);


    # Adicione outros intents conforme necessário, como scroll, add_to_cart, etc.
    
    else:
        print(f"Intent não reconhecido: {intent}")

def process_message(message):
    if message == "OK":
        return "OK"
    else:
        json_command = ET.fromstring(message).find(".//command").text
        command = json.loads(json_command)["nlu"]
        command = json.loads(command)
        print(f"Command received: {command['text']}")
        return command

async def main():
    tts = TTS(FusionAdd="https://127.0.0.1:8000/IM/USER1/APPSHEECH").sendToVoice
    mmi_client_out_add = "wss://127.0.0.1:8005/IM/USER1/APP"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(mmi_client_out_add, ssl=ssl_context) as websocket:

        print("Connected to MMI Client")
        print("AQUIIIIII")

        while not_quit: 
            try:
                msg = await websocket.recv()
                print(f"Received message: {msg}")
                await message_handler(message=msg, tts=tts)
            except Exception as e:
                tts("Ocorreu um erro, a fechar o jogo")
                print(f"Error: {e}")
        
        print("Closing connection")
        await websocket.close()
        print("Connection closed")
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())







# class ActionHandleUnknownCategory(Action):
#     def name(self):
#         return "action_handle_unknown_category"
    
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: dict):

#         category = tracker.get_slot("category")
        
#         if not category:
#             dispatcher.utter_message(text="Não consegui entender a categoria que você quer buscar.")
#             return []


# class ActionSelectProductByPosition(Action):
#     def name(self):
#         return "action_select_product_by_position"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         # Obtém a posição do produto a partir do slot
#         position = tracker.get_slot("position")

#         # Verifica se a posição foi fornecida e é válida
#         if not position:
#             dispatcher.utter_message(text="Desculpe, não entendi a posição do produto que você quer.")
#             return []

#         try:
#             # Converte a posição para inteiro
#             position = int(position) - 1  # Subtrai 1 para ajustar ao índice da lista (começa em 0)
#             print(f"Selecionando produto na posição {position + 1}...")
#             driver = ActionOpenWebsite.driver
#             if not driver:
#                 dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
#                 return []

#             product_retrived = products_retrived[position]

#             driver.get(product_retrived['url'])

#             dispatcher.utter_message(
#                 text=f"O produto na posição {position + 1} foi selecionado."
#             )
#         except ValueError:
#             dispatcher.utter_message(
#                 text="Por favor, informe um número válido para a posição."
#             )
#         except Exception as e:
#             dispatcher.utter_message(
#                 text="Houve um problema ao selecionar o produto. Tente novamente mais tarde."
#             )
#             print(f"Erro ao selecionar produto: {e}")

#         return []
        

# class ActionShowCart(Action):
#     def name(self) -> Text:
#         return "action_show_cart"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         try:
#             driver = ActionOpenWebsite.driver
#             driver.get("https://www.ikea.com/pt/pt/shoppingcart/")
#             dispatcher.utter_message(text="O carrinho foi aberto.")
#         except Exception as e:
#             dispatcher.utter_message(text="Não foi possível abrir o carrinho.")
#             print(f"Erro ao abrir o carrinho: {e}")

#         return	[]

# class ActionShowFavorites(Action):
#     def name(self) -> Text:
#         return "action_show_favorites"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         try:
#             driver = ActionOpenWebsite.driver
#             driver.get("https://www.ikea.com/pt/pt/favourites/")
#             dispatcher.utter_message(text="Os favoritos foram abertos.")
#         except Exception as e:
#             dispatcher.utter_message(text="Não foi possível abrir os favoritos.")
#             print(f"Erro ao abrir os favoritos: {e}")

#         return []


# class ActionAddToCart(Action):
#     def name(self) -> Text:
#         return "action_add_to_cart"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         driver = ActionOpenWebsite.driver

#         if not driver:
#             dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
#             return []
        
#         try:
#             # Localiza o botão de adicionar ao carrinho
#             print("A tentar adicionar ao carrinho...")
#             wait = WebDriverWait(driver, 15)
#             add_to_cart_button = wait.until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--emphasised.pip-btn--fluid"))
#             )

#             print("A clicar no botão de adicionar ao carrinho...")
#             driver.execute_script("arguments[0].click();", add_to_cart_button)
            
#             wait = WebDriverWait(driver, 15)
#             close_button = wait.until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rec-modal-header__close"))
#             )

#             print("A clicar no botão de fechar...")
#             driver.execute_script("arguments[0].click();", close_button)
#             dispatcher.utter_message(text="O produto foi adicionado ao carrinho.")
#         except Exception as e:
#             print("ERROOOOOOO")
#             dispatcher.utter_message(text="Não foi possível adicionar o produto ao carrinho.")
#             print(f"Erro ao adicionar ao carrinho: {e}")


#         return []

# class ActionAddToFavorites(Action):
#     def name(self) -> Text:
#         return "action_add_to_favorites"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         driver = ActionOpenWebsite.driver

#         if not driver:
#             dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
#             return []

#         try:
#             # Locate the "Add to Favorites" button
#             print("A tentar adicionar aos favoritos...")
#             wait = WebDriverWait(driver, 15)
#             add_to_favorites_button = wait.until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--small.pip-btn--icon-primary-inverse.pip-favourite-button"))
#             )

#             print("A clicar no botão de adicionar aos favoritos...")
#             driver.execute_script("arguments[0].click();", add_to_favorites_button)
#             dispatcher.utter_message(text="O produto foi adicionado aos favoritos.")
#         except Exception as e:
#             dispatcher.utter_message(text="Não foi possível adicionar o produto aos favoritos.")
#             print(f"Erro ao adicionar aos favoritos: {e}")

#         return []
