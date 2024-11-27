import http.client
import json
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from typing import Any, Text, Dict, List
import unicodedata
import time

products_retrived = []

class ActionShowProducts(Action):
    def name(self):
        return "action_show_products"
    # Remover acentos da string
    def remove_accents(self, input_str):
        if input_str is not None:
            # Transforma em formato Unicode Normalizado e remove caracteres acentuados
            nfkd_form = unicodedata.normalize('NFKD', input_str)
            return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        return None
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        # Obtém a categoria da entidade "category"
        category = tracker.get_slot("category")

        #remove acentos qualquer tipo de acento
        category2 = self.remove_accents(category)
      
        if not category:
            dispatcher.utter_message(text="Não consegui entender a categoria que você quer buscar.")
            return []

        try:
            
            print("A iniciar pedido:")
            
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
                text="Desculpe, houve um problema ao procurar os produtos. Tente novamente mais tarde."
            )
            print(f"Erro na integração com a API do IKEA: {e}")

                # ---- INTEGRAÇÃO COM SELENIUM ----
        try:
            print("Buscando no site da IKEA com Selenium...")

            # Acessa o driver já inicializado
            driver = ActionOpenWebsite.driver  # Certifique-se de que essa variável é global no código

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

            dispatcher.utter_message(text=f"Buscando por '{category}' no site da IKEA...")

        except Exception as e:
            dispatcher.utter_message(
                text="Houve um problema ao realizar a busca no site. Tente novamente mais tarde."
            )
            print(f"Erro no Selenium: {e}")

        return []


class ActionHandleUnknownCategory(Action):
    def name(self):
        return "action_handle_unknown_category"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        category = tracker.get_slot("category")
        
        if not category:
            dispatcher.utter_message(text="Não consegui entender a categoria que você quer buscar.")
            return []

class ActionOpenWebsite(Action):
    driver = None  # Classe armazenará o driver para reutilização

    def name(self) -> Text:
        return "action_open_website"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # URL fixa para o site da IKEA
        website = "https://www.ikea.com/pt/pt/"

        try:
            # Verifica se o driver ainda está ativo ou precisa ser reiniciado
            if not ActionOpenWebsite.driver or not self.is_driver_alive():
                service = Service("C:\\Users\\rober\\Downloads\\chromedriver-win64\\chromedriver.exe")  # Atualize para o caminho correto
                #service = Service("C:\\Users\\Usuario\\Downloads\\chromedriver-win64\\chromedriver.exe")  # Atualize para o caminho correto
                ActionOpenWebsite.driver = webdriver.Chrome(service=service)
            
            # Abre o site
            ActionOpenWebsite.driver.get(website)
            #FULL SCREEN
            ActionOpenWebsite.driver.maximize_window()
            # Aguarda o botão de aceitação de cookies aparecer
            try:
                wait = WebDriverWait(ActionOpenWebsite.driver, 10)
                cookie_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_button.click()
            except Exception:
                dispatcher.utter_message(text="Não foi possível encontrar o botão de aceitação de cookies.")
            
            dispatcher.utter_message(text=f"A abrir o site do IKEA Portugal")
        except Exception as e:
            dispatcher.utter_message(text=f"Erro ao abrir o site: {str(e)}")
        
        return []

    def is_driver_alive(self) -> bool:
        """
        Verifica se o driver do navegador ainda está ativo.
        """
        try:
            # Tenta acessar um atributo do driver para verificar se ele está vivo
            ActionOpenWebsite.driver.title
            return True
        except:
            # O driver não está mais ativo
            self.close_driver()
            return False

    def close_driver(self):
        """
        Fecha o driver se ele estiver inicializado.
        """
        if ActionOpenWebsite.driver:
            try:
                ActionOpenWebsite.driver.quit()
            except Exception:
                pass  # Ignora exceções durante o fechamento
            ActionOpenWebsite.driver = None


class ActionScrollUp(Action):
    def name(self):
        return "action_scroll_up"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        try:
            driver = ActionOpenWebsite.driver  # Certifique-se de que o driver está configurado globalmente
            # Rola a página suavemente para o topo
            driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            dispatcher.utter_message(text="A página foi rolada para cima.")
        except Exception as e:
            dispatcher.utter_message(text="Houve um problema ao rolar a página para cima.")
            print(f"Erro ao rolar para cima: {e}")
        return []

# Ação para "Descer" a página
class ActionScrollDown(Action):
    def name(self):
        return "action_scroll_down"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        try:
            driver = ActionOpenWebsite.driver   # Certifique-se de que o driver está configurado globalmente
            # Rola a página suavemente para baixo
            driver.execute_script("window.scrollBy({top: 500, behavior: 'smooth'});")
            dispatcher.utter_message(text="A página foi rolada para baixo.")
        except Exception as e:
            dispatcher.utter_message(text="Houve um problema ao rolar a página para baixo.")
            print(f"Erro ao rolar para baixo: {e}")
        return []
    

class ActionSelectProductByPosition(Action):
    def name(self):
        return "action_select_product_by_position"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtém a posição do produto a partir do slot
        position = tracker.get_slot("position")

        # Verifica se a posição foi fornecida e é válida
        if not position:
            dispatcher.utter_message(text="Desculpe, não entendi a posição do produto que você quer.")
            return []

        try:
            # Converte a posição para inteiro
            position = int(position) - 1  # Subtrai 1 para ajustar ao índice da lista (começa em 0)
            print(f"Selecionando produto na posição {position + 1}...")
            driver = ActionOpenWebsite.driver
            if not driver:
                dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
                return []

            product_retrived = products_retrived[position]

            driver.get(product_retrived['url'])

            dispatcher.utter_message(
                text=f"O produto na posição {position + 1} foi selecionado."
            )
        except ValueError:
            dispatcher.utter_message(
                text="Por favor, informe um número válido para a posição."
            )
        except Exception as e:
            dispatcher.utter_message(
                text="Houve um problema ao selecionar o produto. Tente novamente mais tarde."
            )
            print(f"Erro ao selecionar produto: {e}")

        return []
        

class ActionShowCart(Action):
    def name(self) -> Text:
        return "action_show_cart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            driver = ActionOpenWebsite.driver
            driver.get("https://www.ikea.com/pt/pt/shoppingcart/")
            dispatcher.utter_message(text="O carrinho foi aberto.")
        except Exception as e:
            dispatcher.utter_message(text="Não foi possível abrir o carrinho.")
            print(f"Erro ao abrir o carrinho: {e}")

        return	[]

class ActionShowFavorites(Action):
    def name(self) -> Text:
        return "action_show_favorites"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            driver = ActionOpenWebsite.driver
            driver.get("https://www.ikea.com/pt/pt/favourites/")
            dispatcher.utter_message(text="Os favoritos foram abertos.")
        except Exception as e:
            dispatcher.utter_message(text="Não foi possível abrir os favoritos.")
            print(f"Erro ao abrir os favoritos: {e}")

        return []


class ActionAddToCart(Action):
    def name(self) -> Text:
        return "action_add_to_cart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        driver = ActionOpenWebsite.driver

        if not driver:
            dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
            return []
        
        try:
            # Localiza o botão de adicionar ao carrinho
            print("A tentar adicionar ao carrinho...")
            wait = WebDriverWait(driver, 15)
            add_to_cart_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--emphasised.pip-btn--fluid"))
            )

            print("A clicar no botão de adicionar ao carrinho...")
            driver.execute_script("arguments[0].click();", add_to_cart_button)
            
            wait = WebDriverWait(driver, 15)
            close_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rec-modal-header__close"))
            )

            print("A clicar no botão de fechar...")
            driver.execute_script("arguments[0].click();", close_button)
            dispatcher.utter_message(text="O produto foi adicionado ao carrinho.")
        except Exception as e:
            print("ERROOOOOOO")
            dispatcher.utter_message(text="Não foi possível adicionar o produto ao carrinho.")
            print(f"Erro ao adicionar ao carrinho: {e}")


        return []

class ActionAddToFavorites(Action):
    def name(self) -> Text:
        return "action_add_to_favorites"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        driver = ActionOpenWebsite.driver

        if not driver:
            dispatcher.utter_message(text="O navegador não está ativo. Abra o site primeiro.")
            return []

        try:
            # Locate the "Add to Favorites" button
            print("A tentar adicionar aos favoritos...")
            wait = WebDriverWait(driver, 15)
            add_to_favorites_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.pip-btn.pip-btn--small.pip-btn--icon-primary-inverse.pip-favourite-button"))
            )

            print("A clicar no botão de adicionar aos favoritos...")
            driver.execute_script("arguments[0].click();", add_to_favorites_button)
            dispatcher.utter_message(text="O produto foi adicionado aos favoritos.")
        except Exception as e:
            dispatcher.utter_message(text="Não foi possível adicionar o produto aos favoritos.")
            print(f"Erro ao adicionar aos favoritos: {e}")

        return []
