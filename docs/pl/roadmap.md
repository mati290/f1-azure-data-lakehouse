# Roadmapa projektu

[English](../roadmap.md) | [Polski](roadmap.md)

## 1. Cel dokumentu

Roadmapa opisuje potencjalny rozwój projektu F1 Azure Data Lakehouse poza zakresem początkowego MVP.

Przyszłe funkcjonalności są propozycjami, a nie zobowiązaniami dotyczącymi terminów wydania.

Każde usprawnienie powinno zostać zrealizowane jako oddzielne GitHub Issue z określonym zakresem i kryteriami akceptacji.

## 2. v1.0.0 – MVP

Status: Końcowy przegląd.

Zakres:

- Pobieranie danych historycznych z REST API.
- Azure Data Lake Storage Gen2.
- Orkiestracja Azure Data Factory.
- Przetwarzanie Databricks Serverless.
- Medallion Architecture.
- Tabele Delta Lake.
- Model wymiarowy Gold.
- Analityka biznesowa SQL.
- Automatyczne testy jakości danych.
- GitHub Actions CI.
- Dashboard Streamlit.
- Dwujęzyczna dokumentacja portfolio.

## 3. v1.1.0 – Niezawodność i analityka

Status: Propozycja.

| Funkcjonalność | Priorytet |
|---|---|
| Automatyczne egzekwowanie asercji SQL | Wysoki |
| Poprawa kompatybilności zależności | Wysoki |
| Automatyczne raportowanie pokrycia testami | Średni |
| Bezpośrednie porównanie kierowców | Średni |
| Automatyzacja odświeżania snapshotu | Średni |
| Interaktywna mapa torów | Niski |

Cel: poprawa niezawodności i możliwości analitycznych bez znaczącego zwiększania złożoności infrastruktury.

## 4. v1.2.0 – Zaawansowany Data Engineering

Status: Propozycja.

| Funkcjonalność | Priorytet |
|---|---|
| Przyrostowe pobieranie i przetwarzanie danych | Wysoki |
| Operacje Delta MERGE | Wysoki |
| Monitorowanie pipeline'ów i alerty | Wysoki |
| Dedykowana tożsamość wykonawcza Job | Wysoki |
| Przypisywanie kosztów do obciążeń | Średni |
| Infrastructure as Code | Średni |
| Automatyczne wdrażanie | Średni |
| Rozszerzona izolacja sieciowa | Średni |
| Slowly Changing Dimensions Type 2 | Niski |

Cel: ocena praktyk inżynieryjnych stosowanych w środowiskach produkcyjnych oraz poprawa skalowalności.

## 5. v2.0.0 – Zaawansowana analityka Formuły 1

Status: Propozycja długoterminowa.

| Funkcjonalność | Priorytet |
|---|---|
| Integracja wyników kwalifikacji | Wysoki |
| Integracja wyników sprintów | Wysoki |
| Integracja OpenF1 API | Wysoki |
| Analiza czasów okrążeń | Średni |
| Analiza strategii opon | Średni |
| Wizualizacja telemetrii | Średni |
| Animowana powtórka wyścigu | Niski |

Cel: rozszerzenie zbioru analitycznego poza historyczne wyniki Grand Prix.

Przed implementacją należy ocenić licencje dodatkowych źródeł, dostępność danych, ograniczenia API oraz wymagania magazynowania.

## 6. Zasady rozwoju

- Zachowanie odtwarzalności istniejącego MVP.
- Unikanie zbędnej złożoności infrastruktury.
- Ocena kosztów przed wprowadzeniem nowych obciążeń chmurowych.
- Utrzymywanie automatycznych testów regresji.
- Dokumentowanie decyzji architektonicznych.
- Weryfikacja bezpieczeństwa i licencjonowania danych.
- Utrzymywanie polskiej i angielskiej dokumentacji portfolio.

## 7. Zarządzanie wydaniami

Proponowana numeracja wersji wykorzystuje zasady Semantic Versioning.

Zakres i terminy przyszłych wydań zależą od ustalonych priorytetów.

GitHub Issues oraz GitHub Projects powinny służyć do zarządzania oddzielnie zdefiniowanymi zadaniami.

## 8. Powiązana dokumentacja

- [Główny README](../../README.pl.md)
- [Architektura rozwiązania](architecture.md)
- [Koszty, bezpieczeństwo i kompromisy techniczne](costs_security_tradeoffs.md)
- [Jakość danych i CI](data_quality_and_ci.md)