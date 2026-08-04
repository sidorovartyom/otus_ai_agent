import os
import sys
import numpy as np
import networkx as nx
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Tuple

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Загружаем переменные из .env файла
load_dotenv()

# --- КОНФИГУРАЦИЯ ---
ANTHROPIC_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
MODEL = os.getenv("ANTHROPIC_MODEL")
CERT_PATH = os.getenv("CERT_PATH")

if not all([ANTHROPIC_AUTH_TOKEN, BASE_URL, MODEL, CERT_PATH]):
    raise ValueError("Пожалуйста, установите все необходимые переменные в .env файле")

# Создаем HTTP клиент с корпоративным сертификатом
http_client = httpx.Client(verify=CERT_PATH)

client = OpenAI(
    base_url=BASE_URL,
    api_key=ANTHROPIC_AUTH_TOKEN,
    http_client=http_client
)

# --- ДАННЫЕ: ИСТОРИЧЕСКИЕ ФУТБОЛЬНЫЕ ДОКУМЕНТЫ ---
DOCUMENTS = [
    {
        "title": "Трансфер Роналду в Реал Мадрид за рекордные 94 млн",
        "text": (
            "В 2009 году Криштиану Роналду совершил переход из Манчестер Юнайтед в Реал Мадрид "
            "за рекордную на тот момент сумму в 94 миллиона евро. Португальский форвард стал "
            "ключевым игроком 'королевского клуба', забив более 450 голов за 9 лет. "
            "Под руководством различных тренеров, включая Зидана, Роналду выиграл 4 Лиги Чемпионов."
        ),
        "mentions": ["Криштиану Роналду", "Реал Мадрид", "Манчестер Юнайтед", "Зинедин Зидан"],
        "keywords": ["трансфер", "рекорд", "форвард", "Лига Чемпионов"],
    },
    {
        "title": "Чудо в Стамбуле: финал ЛЧ 2005",
        "text": (
            "25 мая 2005 года в Стамбуле произошло одно из величайших чудес в истории футбола. "
            "Ливерпуль проигрывал Милану 0-3 к перерыву, но во втором тайме под руководством "
            "тренера Рафы Бенитеса отыграл три мяча за 6 минут. Капитан Стивен Джеррард возглавил "
            "невероятный камбэк. После серии пенальти вратарь Ежи Дудек стал героем, "
            "а Ливерпуль выиграл свою пятую Лигу Чемпионов."
        ),
        "mentions": ["Ливерпуль", "Милан", "Стивен Джеррард", "Рафа Бенитес"],
        "keywords": ["Лига Чемпионов", "камбэк", "финал", "история"],
    },
    {
        "title": "Золотая эра Барселоны при Гвардиоле",
        "text": (
            "С 2008 по 2012 год Барселона под руководством Пепа Гвардиолы доминировала в мировом футболе. "
            "Команда играла в революционный тики-така стиль с низовым пасовым футболом. "
            "Трио Месси, Хави и Иньеста создавало магию на поле. В 2009 году Барса выиграла секстет - "
            "все шесть возможных трофеев. Команда выиграла три Примеры и две Лиги Чемпионов "
            "за этот период."
        ),
        "mentions": ["Барселона", "Пеп Гвардиола", "Лионель Месси", "Хави", "Андрес Иньеста"],
        "keywords": ["тики-така", "тактика", "доминирование", "Ла Лига"],
    },
    {
        "title": "Триумф Ливерпуля под руководством Клоппа",
        "text": (
            "Юрген Клопп пришел в Ливерпуль в 2015 году и возродил клуб. Его агрессивный прессинг "
            "и харизматичное лидерство привели к триумфу в Лиге Чемпионов 2019 года в Мадриде, "
            "где Ливерпуль победил Тоттенхэм. Ключевые игроки - Мохамед Салах, Садио Мане и "
            "Вирджил ван Дейк. В 2020 году Ливерпуль наконец выиграл Премьер-лигу после 30 лет ожидания, "
            "набрав рекордные 99 очков."
        ),
        "mentions": ["Ливерпуль", "Юрген Клопп", "Мохамед Салах", "Вирджил ван Дейк"],
        "keywords": ["прессинг", "АПЛ", "чемпионство", "возрождение"],
    },
    {
        "title": "Легенда Зидана: от игрока до тренера Реала",
        "text": (
            "Зинедин Зидан - икона футбола. Как игрок он выиграл чемпионат мира 1998 года с Францией "
            "и Лигу Чемпионов с Реал Мадрид в 2002. Несмотря на удаление в финале ЧМ 2006, "
            "его карьера легендарна. Как тренер Реала (2016-2018), Зидан достиг невероятного - "
            "три Лиги Чемпионов подряд, что не удавалось никому в современном футболе. "
            "Его работа с Роналду, Модричем и Рамосом создала династию."
        ),
        "mentions": ["Зинедин Зидан", "Реал Мадрид", "Криштиану Роналду", "Франция"],
        "keywords": ["легенда", "тренер", "чемпион мира", "династия"],
    },
    {
        "title": "Непобедимые Арсенала сезона 2003-04",
        "text": (
            "Сезон 2003-04 стал знаковым для английского футбола. Арсенал под руководством "
            "Арсена Венгера прошел весь сезон Премьер-лиги без единого поражения - 26 побед и "
            "12 ничьих. Тьерри Анри забил 30 голов, а Патрик Виейра капитанствовал команду. "
            "Это достижение не повторялось до и после в истории АПЛ. 'Непобедимые' играли "
            "атакующий, техничный футбол, который восхищал болельщиков."
        ),
        "mentions": ["Арсенал", "Арсен Венгер", "Тьерри Анри", "Патрик Виейра"],
        "keywords": ["непобедимые", "АПЛ", "рекорд", "атакующий футбол"],
    },
]


# --- ПОСТРОЕНИЕ ГРАФА ЗНАНИЙ ---
def build_knowledge_graph() -> nx.DiGraph:
    """
    Создает граф знаний с футбольными сущностями и связями.
    Использует networkx для хранения графа в памяти.
    """
    G = nx.DiGraph()

    # Добавляем узлы - Игроки
    players = [
        ("Криштиану Роналду", {"type": "Player", "position": "Форвард"}),
        ("Лионель Месси", {"type": "Player", "position": "Форвард"}),
        ("Стивен Джеррард", {"type": "Player", "position": "Полузащитник"}),
        ("Зинедин Зидан", {"type": "Player", "position": "Полузащитник"}),
        ("Тьерри Анри", {"type": "Player", "position": "Форвард"}),
        ("Патрик Виейра", {"type": "Player", "position": "Полузащитник"}),
        ("Хави", {"type": "Player", "position": "Полузащитник"}),
        ("Андрес Иньеста", {"type": "Player", "position": "Полузащитник"}),
        ("Мохамед Салах", {"type": "Player", "position": "Форвард"}),
        ("Вирджил ван Дейк", {"type": "Player", "position": "Защитник"}),
    ]

    # Добавляем узлы - Клубы
    clubs = [
        ("Реал Мадрид", {"type": "Club", "country": "Испания", "league": "Ла Лига"}),
        ("Барселона", {"type": "Club", "country": "Испания", "league": "Ла Лига"}),
        ("Манчестер Юнайтед", {"type": "Club", "country": "Англия", "league": "АПЛ"}),
        ("Ливерпуль", {"type": "Club", "country": "Англия", "league": "АПЛ"}),
        ("Арсенал", {"type": "Club", "country": "Англия", "league": "АПЛ"}),
        ("Милан", {"type": "Club", "country": "Италия", "league": "Серия А"}),
    ]

    # Добавляем узлы - Тренеры
    coaches = [
        ("Пеп Гвардиола", {"type": "Coach"}),
        ("Юрген Клопп", {"type": "Coach"}),
        ("Рафа Бенитес", {"type": "Coach"}),
        ("Арсен Венгер", {"type": "Coach"}),
    ]

    # Добавляем узлы - Лиги
    leagues = [
        ("Ла Лига", {"type": "League", "country": "Испания"}),
        ("АПЛ", {"type": "League", "country": "Англия"}),
        ("Серия А", {"type": "League", "country": "Италия"}),
    ]

    # Добавляем все узлы в граф
    G.add_nodes_from(players)
    G.add_nodes_from(clubs)
    G.add_nodes_from(coaches)
    G.add_nodes_from(leagues)

    # Добавляем связи между узлами
    edges = [
        # Игроки играют за клубы (текущие или исторические)
        ("Криштиану Роналду", "Реал Мадрид", {"relation": "PLAYED_FOR", "years": "2009-2018"}),
        ("Криштиану Роналду", "Манчестер Юнайтед", {"relation": "PLAYED_FOR", "years": "2003-2009"}),
        ("Лионель Месси", "Барселона", {"relation": "PLAYED_FOR", "years": "2004-2021"}),
        ("Стивен Джеррард", "Ливерпуль", {"relation": "PLAYED_FOR", "years": "1998-2015"}),
        ("Тьерри Анри", "Арсенал", {"relation": "PLAYED_FOR", "years": "1999-2007"}),
        ("Патрик Виейра", "Арсенал", {"relation": "PLAYED_FOR", "years": "1996-2005"}),
        ("Хави", "Барселона", {"relation": "PLAYED_FOR", "years": "1998-2015"}),
        ("Андрес Иньеста", "Барселона", {"relation": "PLAYED_FOR", "years": "2002-2018"}),
        ("Мохамед Салах", "Ливерпуль", {"relation": "PLAYED_FOR", "years": "2017-2026"}),
        ("Вирджил ван Дейк", "Ливерпуль", {"relation": "PLAYS_FOR", "years": "2018-present"}),

        # Тренеры тренируют клубы
        ("Пеп Гвардиола", "Барселона", {"relation": "COACHED", "years": "2008-2012"}),
        ("Юрген Клопп", "Ливерпуль", {"relation": "COACHED", "years": "2015-2024"}),
        ("Рафа Бенитес", "Ливерпуль", {"relation": "COACHED", "years": "2004-2010"}),
        ("Арсен Венгер", "Арсенал", {"relation": "COACHED", "years": "1996-2018"}),

        # Зидан как игрок и тренер
        ("Зинедин Зидан", "Реал Мадрид", {"relation": "PLAYED_FOR", "years": "2001-2006"}),
        ("Зинедин Зидан", "Реал Мадрид", {"relation": "COACHED", "years": "2016-2018, 2019-2021"}),

        # Клубы играют в лигах
        ("Реал Мадрид", "Ла Лига", {"relation": "PLAYS_IN"}),
        ("Барселона", "Ла Лига", {"relation": "PLAYS_IN"}),
        ("Манчестер Юнайтед", "АПЛ", {"relation": "PLAYS_IN"}),
        ("Ливерпуль", "АПЛ", {"relation": "PLAYS_IN"}),
        ("Арсенал", "АПЛ", {"relation": "PLAYS_IN"}),
        ("Милан", "Серия А", {"relation": "PLAYS_IN"}),

        # Конкуренция между клубами (дерби, исторические соперники)
        ("Реал Мадрид", "Барселона", {"relation": "COMPETES_WITH", "derby": "El Clasico"}),
        ("Барселона", "Реал Мадрид", {"relation": "COMPETES_WITH", "derby": "El Clasico"}),
        ("Ливерпуль", "Манчестер Юнайтед", {"relation": "COMPETES_WITH", "derby": "North West Derby"}),
        ("Манчестер Юнайтед", "Ливерпуль", {"relation": "COMPETES_WITH", "derby": "North West Derby"}),
    ]

    G.add_edges_from([(u, v, d) for u, v, d in edges])

    return G


# --- ВЕКТОРНЫЙ ПОИСК ---
def get_embedding(text: str) -> np.ndarray:
    """
    Получает векторное представление (эмбеддинг) текста через API.
    Использует модель text-embedding-ada-002 или аналог.
    """
    try:
        # Используем OpenAI-совместимый API для получения эмбеддингов
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"  # или другая модель эмбеддингов
        )
        embedding = response.data[0].embedding
        return np.array(embedding)
    except Exception as e:
        print(f"Ошибка при получении эмбеддинга: {e}")
        # Возвращаем случайный вектор как fallback
        return np.random.rand(1536)  # ada-002 дает 1536 размерность


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Вычисляет косинусное сходство между двумя векторами.
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def vector_search(query: str, documents: List[Dict], top_k: int = 3) -> List[Tuple[Dict, float]]:
    """
    Выполняет векторный поиск по документам.
    Возвращает top_k наиболее релевантных документов с их оценками сходства.
    """
    print(f"\n🔍 ВЕКТОРНЫЙ ПОИСК: '{query}'")

    # Получаем эмбеддинг запроса
    query_embedding = get_embedding(query)

    # Вычисляем эмбеддинги для всех документов и их сходство с запросом
    results = []
    for doc in documents:
        doc_text = f"{doc['title']}. {doc['text']}"
        doc_embedding = get_embedding(doc_text)
        similarity = cosine_similarity(query_embedding, doc_embedding)
        results.append((doc, similarity))

    # Сортируем по убыванию сходства
    results.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем top_k результатов
    top_results = results[:top_k]

    print(f"Найдено {len(top_results)} релевантных документов:")
    for i, (doc, score) in enumerate(top_results, 1):
        print(f"  {i}. {doc['title']} (сходство: {score:.3f})")

    return top_results


# --- ГРАФОВЫЙ ПОИСК ---
def find_related_entities(graph: nx.DiGraph, entity: str, relation_type: str = None) -> List[Tuple[str, Dict]]:
    """
    Находит сущности, связанные с заданной через определенный тип связи.
    """
    if entity not in graph:
        return []

    related = []
    for neighbor in graph.neighbors(entity):
        edge_data = graph.get_edge_data(entity, neighbor)
        if relation_type is None or edge_data.get('relation') == relation_type:
            node_data = graph.nodes[neighbor]
            related.append((neighbor, {**node_data, **edge_data}))

    return related


def find_entities_by_type(graph: nx.DiGraph, entity_type: str) -> List[str]:
    """
    Находит все сущности определенного типа в графе.
    """
    return [node for node, data in graph.nodes(data=True) if data.get('type') == entity_type]


def graph_search(graph: nx.DiGraph, query_entities: List[str]) -> Dict[str, List]:
    """
    Выполняет поиск по графу для заданных сущностей.
    Возвращает информацию о связях найденных сущностей.
    """
    print(f"\n🕸️ ГРАФОВЫЙ ПОИСК для сущностей: {query_entities}")

    results = {}
    for entity in query_entities:
        if entity in graph:
            # Находим все связи данной сущности
            related = []
            for neighbor in graph.neighbors(entity):
                edge_data = graph.get_edge_data(entity, neighbor)
                node_data = graph.nodes[neighbor]
                related.append({
                    "entity": neighbor,
                    "type": node_data.get("type"),
                    "relation": edge_data.get("relation"),
                    "details": {k: v for k, v in edge_data.items() if k != "relation"}
                })

            results[entity] = related
            print(f"\n  📍 {entity}:")
            for rel in related:
                print(f"    → {rel['relation']}: {rel['entity']} ({rel['type']})")

    return results


# --- ГИБРИДНЫЙ ПОИСК ---
def hybrid_search(query: str, documents: List[Dict], graph: nx.DiGraph, top_k: int = 2) -> Dict:
    """
    Выполняет гибридный поиск: сначала векторный поиск по документам,
    затем обогащает результаты информацией из графа знаний.
    """
    print(f"\n{'='*70}")
    print(f"🔄 ГИБРИДНЫЙ ПОИСК: '{query}'")
    print(f"{'='*70}")

    # Шаг 1: Векторный поиск
    vector_results = vector_search(query, documents, top_k=top_k)

    # Шаг 2: Извлекаем упомянутые сущности из найденных документов
    mentioned_entities = set()
    for doc, score in vector_results:
        for mention in doc.get("mentions", []):
            mentioned_entities.add(mention)

    print(f"\n📝 Извлечены сущности из документов: {list(mentioned_entities)}")

    # Шаг 3: Обогащаем контекст информацией из графа
    graph_context = graph_search(graph, list(mentioned_entities))

    # Формируем итоговый контекст
    result = {
        "query": query,
        "vector_results": [
            {"title": doc["title"], "text": doc["text"], "score": score}
            for doc, score in vector_results
        ],
        "graph_context": graph_context,
        "mentioned_entities": list(mentioned_entities)
    }

    return result


def format_context_for_llm(hybrid_result: Dict) -> str:
    """
    Форматирует результаты гибридного поиска в текст для LLM.
    """
    parts = []

    parts.append("=== НАЙДЕННЫЕ ДОКУМЕНТЫ ===\n")
    for i, doc in enumerate(hybrid_result["vector_results"], 1):
        parts.append(f"{i}. {doc['title']} (релевантность: {doc['score']:.3f})")
        parts.append(f"   {doc['text']}\n")

    parts.append("\n=== СВЯЗИ В ГРАФЕ ЗНАНИЙ ===\n")
    for entity, relations in hybrid_result["graph_context"].items():
        parts.append(f"\n{entity}:")
        for rel in relations:
            details = ", ".join(f"{k}={v}" for k, v in rel["details"].items())
            parts.append(f"  - {rel['relation']} → {rel['entity']} ({rel['type']}) {details}")

    return "\n".join(parts)


# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    print("⚽ Система памяти агента на основе футбольных данных")
    print("="*70)

    # Инициализация
    print("\n📊 Загрузка данных...")
    graph = build_knowledge_graph()
    print(f"✅ Граф построен: {graph.number_of_nodes()} узлов, {graph.number_of_edges()} связей")
    print(f"✅ Загружено {len(DOCUMENTS)} документов")

    # Примеры запросов
    queries = [
        "Какие достижения у Роналду в Реале?",
        "Расскажи о тактике Барселоны при Гвардиоле",
        "Кто тренировал Ливерпуль во время чуда в Стамбуле?",
    ]

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ")
    print("="*70)

    for query in queries:
        # Выполняем гибридный поиск
        result = hybrid_search(query, DOCUMENTS, graph, top_k=2)

        # Форматируем контекст
        context = format_context_for_llm(result)

        print(f"\n📋 ИТОГОВЫЙ КОНТЕКСТ ДЛЯ LLM:")
        print("-" * 70)
        print(context)
        print("-" * 70)
        print("\n" + "="*70)


if __name__ == "__main__":
    main()
