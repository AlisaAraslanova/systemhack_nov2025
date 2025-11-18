import requests
from langchain_gigachat.chat_models import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, render_template, request
import langchain
from dotenv import load_dotenv
import os
from count_mistakes import get_mistakes

load_dotenv()

langchain.verbose = False
langchain.debug = False
langchain.llm_cache = False

def _generate_report(llm, html_page, mistakes) -> str:

    try:
        system_template = '''
        Ты - умный помощник, который разбирается в инклюзивности сайтов.
        Проанализируй предложенную html-страницу и сформируй отчёт о найденных ошибках в формате markdown. 
        Отчёт должен содержать строки кода сайта, указывающие на найденные ошибки, и рекомендации по исправлению этих ошибок
        На вход подаются список найденных ошибок и сам html-код, на выходе: отчёт в формате markdown.
        Отчёт должен быть на русском языке!
        '''

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", "Список найденных ошибок: {mistakes} \n {html_page}")
        ])

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"mistakes": mistakes, "html_page": html_page})
        return result
    except Exception as e:
        print(f"Ошибка в _generate_report: {e}")
        return "Отчёт не удалось сгенерировать."
    
app = Flask(__name__)
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            # Получение HTML-контента сайта
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text

            llm = GigaChat(
                model="GigaChat-2-Max",
                temperature=0.7,
                credentials=os.getenv("SBERBANK_API_KEY"),
                verify_ssl_certs=False
            )

            score, found_mistakes = get_mistakes(llm, html_content)
            markdown_report = _generate_report(llm, html_content, ", ".join(found_mistakes["mistakes_list"]))
            return render_template('result.html', report=markdown_report, score=score, 
                                   critical_errors=found_mistakes["critical"], noncritical_errors=found_mistakes["non-critical"])

        except requests.exceptions.RequestException as e:
            return f"Ошибка при загрузке страницы: {e}"
        except Exception as e:
            return f"Ошибка при анализе: {e}"
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
        

