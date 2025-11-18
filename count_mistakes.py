from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import json



def _generate_mistakes(llm, html_page, mistakes):

    try:
        system_template = '''
        Ты - умный помощник, который разбирается в инклюзивности сайтов.
        Проанализируй предложенную html-страницу на предложенные в списке возможные ошибки и выведи список найденных ошибок НА РУССКОМ ЯЗЫКЕ в формате python-списка.
        Ввод: список возможных ошибок, html-текст. Вывод: python-список с найденными ошибками на html-странице из введённого списка.
        Выводи только найденные ошибки, не придумывай своих ошибок, не выводи ничего, кроме python-списка.
        Названия найденных ошибок должны совпадать с названиями ошибок из введённого текста.
        Список найденных ошибок должен быть на русском языке!
        '''

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", "Список возможных ошибок: {mistakes} \n {html_page}")
        ])

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"mistakes": mistakes, "html_page": html_page})
        return result
    except Exception as e:
        print(f"Ошибка в _generate_mistakes: {e}")
        return "Ошибки не удалось сгенерировать"
    
    
def get_mistakes(llm, html_page):
    with open('mistakes.json', 'r', encoding='utf-8') as f:
        mistakes = json.load(f)

    score = 34
    found_mistakes = {}
    found_mistakes["critical"] = 0
    found_mistakes["non-critical"] = 0
    found_mistakes["mistakes_list"] = []

    critical_mistakes = _generate_mistakes(llm, html_page, ", ".join(mistakes["critical"]))
    if critical_mistakes != "Ошибки не удалось сгенерировать":
        for mistake in mistakes["critical"]:
            if mistake in critical_mistakes:
                score -= 2
                found_mistakes["mistakes_list"].append(mistake)
                found_mistakes["critical"] += 1

    noncritical_mistakes = _generate_mistakes(llm, html_page, ", ".join(mistakes["non-critical"]))

    if noncritical_mistakes != "Ошибки не удалось сгенерировать":
        for mistake in mistakes["non-critical"]:
            if mistake in noncritical_mistakes:
                score -= 1
                found_mistakes["mistakes_list"].append(mistake)
                found_mistakes["non-critical"] += 1

    final_score = int((score/34)*100)

    return final_score, found_mistakes

    
    