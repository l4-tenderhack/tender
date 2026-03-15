#!/usr/bin/env python3
"""
Скрипт для тестирования ручки /api/v1/cte-search
Анализирует релевантность результатов и выбросы в ценах
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import statistics

# Конфигурация
URLS = {
    "local": "http://localhost:8000",
    "prod": "https://akim.larek.tech",
}
OUTPUT_FILE = "cte_search_compare.json"
REPORT_FILE = "cte_search_compare.txt"

# Примеры поисковых запросов из документации
SEARCH_QUERIES = [
    # === 1. По конкретным товарам (точные совпадения) ===
    {
        "name": "Точный поиск: Мусорные пакеты 35л",
        "query": "Мусорные пакеты 35л",
        "expected_category": "Пакеты полимерные",
        "expected_manufacturer": "СПРИНТ-ПЛАСТ"
    },
    {
        "name": "Точный поиск: Огурцы консервированные",
        "query": "Огурцы консервированные Конэкс",
        "expected_category": "Овощи соленые, квашеные, вяленые",
        "expected_manufacturer": "КОНЭКС"
    },
    {
        "name": "Точный поиск: Радиостанция",
        "query": "Радиостанция носимая аналоговая Шеврон",
        "expected_category": "Радиостанции цифровые",
        "expected_manufacturer": 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АЙТИ-ТРЕЙД"'
    },

    # === 2. По производителям ===
    {
        "name": "По производителю: СПРИНТ-ПЛАСТ",
        "query": "товары от СПРИНТ-ПЛАСТ",
        "expected_manufacturer": "СПРИНТ-ПЛАСТ"
    },
    {
        "name": "По производителю: ХЕМА",
        "query": "ХЕМА реагенты",
        "expected_manufacturer": "ООО ХЕМА"
    },

    # === 3. По категориям ===
    {
        "name": "По категории: Пакеты полимерные",
        "query": "Пакеты полимерные",
        "expected_category": "Пакеты полимерные"
    },
    {
        "name": "По категории: Наборы реактивов",
        "query": "Наборы реактивов реагентов",
        "expected_category": "Наборы реактивов/реагентов"
    },
    {
        "name": "По категории: Тетради для слабовидящих",
        "query": "Тетради для слабовидящих",
        "expected_category": "Тетради для слабовидящих"
    },

    # === 4. По характеристикам ===
    {
        "name": "По характеристикам: Пакеты черного цвета",
        "query": "Пакеты черного цвета",
        "expected_category": "Пакеты полимерные"
    },
    {
        "name": "По характеристикам: Наборы на 96 тестов",
        "query": "Наборы реагентов 96 тестов",
        "expected_category": "Наборы реактивов/реагентов"
    },

    # === 5. По объему упаковки ===
    {
        "name": "По объему: пакеты 35 литров",
        "query": "Пакеты объемом 35 литров",
        "expected_category": "Пакеты полимерные"
    },

    # === 6. Комбинированные запросы ===
    {
        "name": "Комбинированный: мусорные пакеты СПРИНТ-ПЛАСТ черного цвета",
        "query": "мусорные пакеты СПРИНТ-ПЛАСТ черного цвета",
        "expected_category": "Пакеты полимерные",
        "expected_manufacturer": "СПРИНТ-ПЛАСТ"
    },
    {
        "name": "Комбинированный: Тетради ЛОГОСВОС размером 170х205",
        "query": "Тетради ЛОГОСВОС размером 170х205",
        "expected_manufacturer": 'ООО "ИПТК "ЛОГОСВОС"'
    },

    # === 7. Поиск по назначению ===
    {
        "name": "По назначению: товары для слабовидящих",
        "query": "Товары для слабовидящих",
        "expected_category": "Тетради для слабовидящих"
    },
    {
        "name": "По назначению: реагенты для иммуноферментного анализа",
        "query": "реагенты для иммуноферментного анализа",
        "expected_category": "Наборы реактивов/реагентов"
    },
]


@dataclass
class SearchResult:
    """Результат одного поиска"""
    test_name: str
    query: str
    timestamp: str
    status_code: int
    success: bool
    total_results: int
    execution_time_ms: float
    server_elapsed_ms: float
    first_result_relevance: float
    price_outliers_count: int
    price_std_dev: float
    error_message: str = None
    matched_ctes: List[str] = None
    matched_cte_names: List[str] = None
    matched_scores: List[float] = None
    prices: List[float] = None


class CteSearchTester:
    """Класс для тестирования ручки cte-search"""

    def __init__(self, api_endpoint: str, label: str, output_file: str, report_file: str):
        self.api_endpoint = api_endpoint
        self.label = label
        self.output_file = output_file
        self.report_file = report_file
        self.results: List[SearchResult] = []
        self.session = requests.Session()

    def perform_search(self, query_config: Dict[str, Any]) -> SearchResult:
        """Выполнить одно поисковое запрос и вернуть результаты"""

        test_name = query_config.get("name", "Unknown test")
        query_text = query_config.get("query", "")

        print(f"\n{'=' * 70}")
        print(f"Тест: {test_name}")
        print(f"Запрос: {query_text}")
        print(f"{'=' * 70}")

        try:
            # Формируем payload
            payload = {
                "query": query_text,
                "n": 10,  # Получаем топ-10 результатов
                # Опционально: фильтры по дате, региону, ИНН
                # "date_from": (datetime.now() - timedelta(days=365)).date().isoformat(),
                # "date_to": datetime.now().date().isoformat(),
            }

            # Выполняем запрос
            start_time = time.time()
            response = self.session.post(self.api_endpoint, json=payload)
            execution_time = (time.time() - start_time) * 1000  # В миллисекундах

            status_code = response.status_code
            success = status_code == 200

            if success:
                data = response.json()

                # Извлекаем данные
                matched_ctes = [cte["cte_id"] for cte in data.get("matched_ctes", [])]
                cte_names = [cte["cte_name"] for cte in data.get("matched_ctes", [])]
                cte_scores = [cte.get("score", 0.0) for cte in data.get("matched_ctes", [])]

                # Извлекаем цены из контрактов
                prices = []
                for contract in data.get("contracts", []):
                    for item in contract.get("items", []):
                        unit_price = item.get("unit_price")
                        if unit_price:
                            try:
                                prices.append(float(unit_price))
                            except (ValueError, TypeError):
                                pass

                # Анализируем цены на выбросы
                price_outliers = self._detect_outliers(prices) if prices else []
                price_std_dev = statistics.stdev(prices) if len(prices) > 1 else 0.0

                # Оцениваем релевантность первого результата
                first_relevance = self._calculate_first_result_relevance(
                    data.get("matched_ctes", []),
                    query_config,
                    data.get("contracts", [])
                )

                server_elapsed = data.get("elapsed_ms")

                print(f"✓ Статус: {status_code}")
                print(f"✓ Результатов найдено: {len(matched_ctes)}")
                print(f"✓ Контрактов: {data.get('total_contracts', 0)}")
                print(f"✓ Уникальных цен: {len(prices)}")
                print(f"✓ Выявлено выбросов: {len(price_outliers)}")
                print(f"✓ Стандартное отклонение цен: {price_std_dev:.2f}")
                print(f"✓ Время (клиент): {execution_time:.2f} мс")
                if server_elapsed is not None:
                    print(f"✓ Время (сервер): {server_elapsed:.1f} мс")
                print(f"✓ Релевантность первого результата: {first_relevance:.2%}")

                if matched_ctes:
                    print(f"\nНайденные КТЕ (ID):")
                    for cte_id, cte_name in zip(matched_ctes[:5], cte_names[:5]):
                        print(f"  - {cte_id}: {cte_name}")

                if prices:
                    print(f"\nСтатистика по ценам:")
                    print(f"  Мин: {min(prices):.2f}")
                    print(f"  Макс: {max(prices):.2f}")
                    print(f"  Средн: {statistics.mean(prices):.2f}")
                    print(f"  Медиана: {statistics.median(prices):.2f}")
                    if price_outliers:
                        print(f"  Выбросы (IQR метод): {price_outliers}")

                result = SearchResult(
                    test_name=test_name,
                    query=query_text,
                    timestamp=datetime.now().isoformat(),
                    status_code=status_code,
                    success=True,
                    total_results=len(matched_ctes),
                    execution_time_ms=execution_time,
                    server_elapsed_ms=server_elapsed if server_elapsed is not None else 0.0,
                    first_result_relevance=first_relevance,
                    price_outliers_count=len(price_outliers),
                    price_std_dev=price_std_dev,
                    matched_ctes=matched_ctes,
                    matched_cte_names=cte_names,
                    matched_scores=cte_scores,
                    prices=prices
                )
            else:
                error_msg = response.text
                print(f"✗ Ошибка: {status_code}")
                print(f"✗ Сообщение: {error_msg}")

                result = SearchResult(
                    test_name=test_name,
                    query=query_text,
                    timestamp=datetime.now().isoformat(),
                    status_code=status_code,
                    success=False,
                    total_results=0,
                    execution_time_ms=execution_time,
                    server_elapsed_ms=0.0,
                    first_result_relevance=0.0,
                    price_outliers_count=0,
                    price_std_dev=0.0,
                    error_message=error_msg
                )

        except Exception as e:
            error_msg = str(e)
            print(f"✗ Исключение: {error_msg}")

            result = SearchResult(
                test_name=test_name,
                query=query_text,
                timestamp=datetime.now().isoformat(),
                status_code=0,
                success=False,
                total_results=0,
                execution_time_ms=0.0,
                server_elapsed_ms=0.0,
                first_result_relevance=0.0,
                price_outliers_count=0,
                price_std_dev=0.0,
                error_message=error_msg
            )

        self.results.append(result)
        return result

    def _detect_outliers(self, values: List[float], method: str = "iqr") -> List[float]:
        """Выявить выбросы в списке значений"""
        if len(values) < 4:
            return []

        sorted_vals = sorted(values)

        if method == "iqr":
            # Метод межквартильного размаха (IQR)
            q1_idx = len(sorted_vals) // 4
            q3_idx = 3 * len(sorted_vals) // 4

            q1 = sorted_vals[q1_idx]
            q3 = sorted_vals[q3_idx]
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = [v for v in values if v < lower_bound or v > upper_bound]
        else:
            # Метод стандартного отклонения (3-sigma rule)
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values)

            lower_bound = mean - 3 * std_dev
            upper_bound = mean + 3 * std_dev

            outliers = [v for v in values if v < lower_bound or v > upper_bound]

        return outliers

    def _calculate_first_result_relevance(
            self,
            matched_ctes: List[Dict],
            query_config: Dict,
            contracts: List[Dict]
    ) -> float:
        """Вычислить релевантность первого результата (0.0-1.0)"""

        if not matched_ctes:
            return 0.0

        first_cte = matched_ctes[0]
        relevance_score = 0.0
        total_factors = 0

        # Проверяем категорию
        if "expected_category" in query_config:
            expected_category = query_config["expected_category"]
            actual_category = first_cte.get("category", "")

            # Точное совпадение - 100%
            if expected_category.lower() in actual_category.lower():
                relevance_score += 1.0
            # Частичное совпадение - 50%
            elif any(word in actual_category.lower()
                     for word in expected_category.lower().split()):
                relevance_score += 0.5
            # Без совпадения - 0%
            else:
                relevance_score += 0.0

            total_factors += 1

        # Проверяем производителя
        if "expected_manufacturer" in query_config:
            expected_mfr = query_config["expected_manufacturer"]
            actual_mfr = first_cte.get("manufacturer", "")

            if expected_mfr.lower() in actual_mfr.lower():
                relevance_score += 1.0
            elif any(word in actual_mfr.lower()
                     for word in expected_mfr.lower().split() if len(word) > 2):
                relevance_score += 0.5
            else:
                relevance_score += 0.0

            total_factors += 1

        # Проверяем скор поиска (если есть)
        if "score" in first_cte:
            score = first_cte["score"]
            # Нормализуем скор к 0.0-1.0
            normalized_score = min(score, 1.0)
            relevance_score += normalized_score
            total_factors += 1

        # Если есть контракты с ценами
        if contracts and any(c.get("items") for c in contracts):
            relevance_score += 0.5  # Бонус за наличие ценовых данных
            total_factors += 1

        if total_factors == 0:
            return 0.0

        return relevance_score / total_factors

    def run_all_tests(self):
        """Запустить все тесты"""
        print("\n" + "=" * 70)
        print(f"ТЕСТИРОВАНИЕ [{self.label}] {self.api_endpoint}")
        print("=" * 70)
        print(f"Всего тестов: {len(SEARCH_QUERIES)}")
        print(f"Начало: {datetime.now().isoformat()}")

        for i, query_config in enumerate(SEARCH_QUERIES, 1):
            print(f"\n[{i}/{len(SEARCH_QUERIES)}] ", end="")
            self.perform_search(query_config)
            time.sleep(0.5)  # Задержка между запросами

        print("\n" + "=" * 70)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 70)

    def save_results(self):
        """Сохранить результаты в JSON файл"""
        results_data = []
        for result in self.results:
            result_dict = asdict(result)
            results_data.append(result_dict)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        print(f"✓ Результаты сохранены в: {self.output_file}")

    def generate_report(self):
        """Сгенерировать текстовый отчет"""
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"ОТЧЕТ О ТЕСТИРОВАНИИ [{self.label}]\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Дата и время: {datetime.now().isoformat()}\n")
            f.write(f"API URL: {self.api_endpoint}\n")
            f.write(f"Всего тестов: {len(self.results)}\n\n")

            # === СТАТИСТИКА ОБЩАЯ ===
            f.write("=" * 70 + "\n")
            f.write("1. ОБЩАЯ СТАТИСТИКА\n")
            f.write("=" * 70 + "\n\n")

            successful = sum(1 for r in self.results if r.success)
            failed = len(self.results) - successful

            f.write(
                f"Успешных запросов: {successful}/{len(self.results)} ({successful / len(self.results) * 100:.1f}%)\n")
            f.write(f"Ошибок: {failed}/{len(self.results)} ({failed / len(self.results) * 100:.1f}%)\n\n")

            # === СТАТИСТИКА ПО ВРЕМЕНИ ===
            if any(r.success for r in self.results):
                exec_times = [r.execution_time_ms for r in self.results if r.success]
                server_times = [r.server_elapsed_ms for r in self.results if r.success and r.server_elapsed_ms > 0]

                f.write(f"Время выполнения (клиент):\n")
                f.write(f"  Минимум: {min(exec_times):.2f} мс\n")
                f.write(f"  Максимум: {max(exec_times):.2f} мс\n")
                f.write(f"  Среднее: {statistics.mean(exec_times):.2f} мс\n")
                if len(exec_times) > 1:
                    f.write(f"  Стд.откл: {statistics.stdev(exec_times):.2f} мс\n")
                f.write("\n")

                if server_times:
                    f.write(f"Время выполнения (сервер):\n")
                    f.write(f"  Минимум: {min(server_times):.1f} мс\n")
                    f.write(f"  Максимум: {max(server_times):.1f} мс\n")
                    f.write(f"  Среднее: {statistics.mean(server_times):.1f} мс\n")
                    if len(server_times) > 1:
                        f.write(f"  Стд.откл: {statistics.stdev(server_times):.1f} мс\n")
                    f.write("\n")

            # === СТАТИСТИКА ПО РЕЗУЛЬТАТАМ ===
            f.write("=" * 70 + "\n")
            f.write("2. СТАТИСТИКА ПО РЕЗУЛЬТАТАМ ПОИСКА\n")
            f.write("=" * 70 + "\n\n")

            result_counts = [r.total_results for r in self.results if r.success]
            if result_counts:
                f.write(f"Среднее кол-во результатов: {statistics.mean(result_counts):.1f}\n")
                f.write(f"Макс. кол-во результатов: {max(result_counts)}\n")
                f.write(f"Мин. кол-во результатов: {min(result_counts)}\n\n")

            # === АНАЛИЗ ВЫБРОСОВ ===
            f.write("=" * 70 + "\n")
            f.write("3. АНАЛИЗ ВЫБРОСОВ В ЦЕНАХ\n")
            f.write("=" * 70 + "\n\n")

            outlier_data = [(r.test_name, r.price_outliers_count, r.price_std_dev)
                            for r in self.results if r.success and r.price_outliers_count > 0]

            if outlier_data:
                f.write(f"Тесты с выявленными выбросами: {len(outlier_data)}\n\n")
                for test_name, outlier_count, std_dev in sorted(outlier_data, key=lambda x: x[1], reverse=True):
                    f.write(f"  - {test_name}\n")
                    f.write(f"    Выбросов: {outlier_count}, Стд.откл: {std_dev:.2f}\n")
            else:
                f.write("Выбросов в ценах не обнаружено.\n")

            f.write("\n")

            # === АНАЛИЗ РЕЛЕВАНТНОСТИ ===
            f.write("=" * 70 + "\n")
            f.write("4. АНАЛИЗ РЕЛЕВАНТНОСТИ РЕЗУЛЬТАТОВ\n")
            f.write("=" * 70 + "\n\n")

            relevance_scores = [r.first_result_relevance for r in self.results if r.success]
            if relevance_scores:
                avg_relevance = statistics.mean(relevance_scores)
                f.write(f"Средняя релевантность первого результата: {avg_relevance:.2%}\n\n")

                # Группируем по уровню релевантности
                excellent = sum(1 for s in relevance_scores if s >= 0.8)
                good = sum(1 for s in relevance_scores if 0.6 <= s < 0.8)
                fair = sum(1 for s in relevance_scores if 0.4 <= s < 0.6)
                poor = sum(1 for s in relevance_scores if s < 0.4)

                f.write(f"Распределение по уровню релевантности:\n")
                f.write(f"  Отличная (≥80%): {excellent} тестов\n")
                f.write(f"  Хорошая (60-80%): {good} тестов\n")
                f.write(f"  Средняя (40-60%): {fair} тестов\n")
                f.write(f"  Плохая (<40%): {poor} тестов\n\n")

            # === ДЕТАЛЬНЫЙ РЕЗУЛЬТАТЫ ===
            f.write("=" * 70 + "\n")
            f.write("5. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ КАЖДОГО ТЕСТА\n")
            f.write("=" * 70 + "\n\n")

            for i, result in enumerate(self.results, 1):
                f.write(f"[{i}] {result.test_name}\n")
                f.write(f"    Запрос: {result.query}\n")
                f.write(f"    Статус: {'✓ Успех' if result.success else '✗ Ошибка'}\n")

                if result.success:
                    f.write(f"    Результатов: {result.total_results}\n")
                    f.write(f"    Время (клиент): {result.execution_time_ms:.2f} мс\n")
                    if result.server_elapsed_ms > 0:
                        f.write(f"    Время (сервер): {result.server_elapsed_ms:.1f} мс\n")
                    f.write(f"    Выбросов: {result.price_outliers_count}\n")
                    f.write(f"    Релевантность: {result.first_result_relevance:.2%}\n")
                else:
                    f.write(f"    Ошибка: {result.error_message}\n")

                f.write("\n")

        print(f"✓ Отчет сохранен в: {self.report_file}")


def _print_summary(label: str, tester: CteSearchTester):
    successful = sum(1 for r in tester.results if r.success)
    print(f"\n  [{label}] Успешных: {successful}/{len(tester.results)}")
    if any(r.success for r in tester.results):
        with_outliers = sum(1 for r in tester.results if r.success and r.price_outliers_count > 0)
        avg_relevance = statistics.mean([r.first_result_relevance for r in tester.results if r.success])
        exec_times = [r.execution_time_ms for r in tester.results if r.success]
        server_times = [r.server_elapsed_ms for r in tester.results if r.success and r.server_elapsed_ms > 0]
        print(f"  [{label}] Средняя релевантность: {avg_relevance:.2%}")
        print(f"  [{label}] Среднее время (клиент): {statistics.mean(exec_times):.0f} мс")
        if server_times:
            print(f"  [{label}] Среднее время (сервер): {statistics.mean(server_times):.0f} мс")
        print(f"  [{label}] Тестов с выбросами: {with_outliers}/{successful}")


def main():
    """Главная функция — запуск тестов на обоих URL и сравнение"""
    testers: Dict[str, CteSearchTester] = {}

    for label, base_url in URLS.items():
        endpoint = f"{base_url}/api/v1/cte-search"
        tester = CteSearchTester(
            api_endpoint=endpoint,
            label=label,
            output_file=f"cte_search_{label}.json",
            report_file=f"cte_search_{label}.txt",
        )

        try:
            print(f"Проверка доступности [{label}] {base_url} ...")
            response = requests.get(f"{base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ [{label}] доступен")
            else:
                print(f"✗ [{label}] статус {response.status_code}")
        except Exception as e:
            print(f"✗ [{label}] недоступен: {e}")

        tester.run_all_tests()
        tester.save_results()
        tester.generate_report()
        testers[label] = tester

    # Сравнительная сводка
    print("\n" + "=" * 70)
    print("СРАВНИТЕЛЬНАЯ СВОДКА")
    print("=" * 70)

    for label, tester in testers.items():
        _print_summary(label, tester)

    # Попарное сравнение релевантности по каждому тесту
    labels = list(testers.keys())
    if len(labels) == 2:
        a, b = labels
        ta, tb = testers[a], testers[b]
        print(f"\n  {'Тест':<55} {a:>8} {b:>8}  delta")
        print("  " + "-" * 85)
        for ra, rb in zip(ta.results, tb.results):
            if ra.success and rb.success:
                delta = ra.first_result_relevance - rb.first_result_relevance
                sign = "+" if delta > 0 else ""
                print(
                    f"  {ra.test_name:<55} {ra.first_result_relevance:>7.1%} {rb.first_result_relevance:>7.1%}  {sign}{delta:.1%}"
                )

    # Сводная таблица ответов
    if len(labels) == 2:
        a, b = labels
        ta, tb = testers[a], testers[b]
        print("\n" + "=" * 70)
        print("СВОДНАЯ ТАБЛИЦА ОТВЕТОВ")
        print("=" * 70)

        for ra, rb in zip(ta.results, tb.results):
            print(f"\n--- {ra.test_name} ---")
            print(f"    Запрос: {ra.query}")

            max_rows = max(
                len(ra.matched_cte_names or []),
                len(rb.matched_cte_names or []),
            )
            if max_rows == 0:
                print(f"    Нет результатов")
                continue

            print(f"    {'#':<4} {'[' + a + ']':<50} {'score':>6}  {'[' + b + ']':<50} {'score':>6}")
            print(f"    {'-'*4} {'-'*50} {'-'*6}  {'-'*50} {'-'*6}")

            names_a = ra.matched_cte_names or []
            names_b = rb.matched_cte_names or []
            scores_a = ra.matched_scores or []
            scores_b = rb.matched_scores or []

            for i in range(max_rows):
                na = names_a[i][:48] if i < len(names_a) else ""
                sa = f"{scores_a[i]:.3f}" if i < len(scores_a) else ""
                nb = names_b[i][:48] if i < len(names_b) else ""
                sb = f"{scores_b[i]:.3f}" if i < len(scores_b) else ""
                print(f"    {i+1:<4} {na:<50} {sa:>6}  {nb:<50} {sb:>6}")

            # Время
            ta_client = f"{ra.execution_time_ms:.0f}" if ra.success else "err"
            tb_client = f"{rb.execution_time_ms:.0f}" if rb.success else "err"
            ta_server = f"{ra.server_elapsed_ms:.0f}" if ra.server_elapsed_ms > 0 else "-"
            tb_server = f"{rb.server_elapsed_ms:.0f}" if rb.server_elapsed_ms > 0 else "-"
            print(f"    Время (клиент): {a}={ta_client}мс  {b}={tb_client}мс")
            print(f"    Время (сервер): {a}={ta_server}мс  {b}={tb_server}мс")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()