# Konfiguracja i odtwarzalność projektu

[English](../setup.md) | [Polski](setup.md)

## 1. Wprowadzenie

Projekt F1 Performance Analytics umożliwia trzy niezależne sposoby eksploracji rozwiązania.

| Tryb | Wymaga Azure | Przeznaczenie |
|---|---|---|
| Lokalny dashboard | Nie | Analiza historycznych wyników Formuły 1 |
| Lokalne testy automatyczne | Nie | Walidacja transformacji i logiki biznesowej |
| Pełne wdrożenie Azure | Tak | Odtworzenie kompletnego pipeline'u danych |

Rekomendowanym punktem startowym dla rekruterów i osób oceniających projekt jest lokalny dashboard.

## 2. Wymagania wstępne

### Lokalny dashboard

- Python 3.12
- Git
- Dostęp do Internetu w celu instalacji zależności
- Przeglądarka internetowa

### Testy automatyczne

- Python 3.12
- Java 17
- Git

### Pełne wdrożenie Azure

- Aktywna subskrypcja Azure
- Uprawnienia do tworzenia zasobów Azure
- Azure Data Factory
- Azure Data Lake Storage Gen2
- Azure Databricks Premium
- Dostępność Serverless Compute
- Unity Catalog
- Konto GitHub

Visual Studio Code jest rekomendowanym, ale niewymaganym środowiskiem programistycznym.

## 3. Klonowanie repozytorium

```bash
git clone https://github.com/mati290/f1-azure-data-lakehouse.git
cd f1-azure-data-lakehouse
```

## 4. Konfiguracja środowiska Python

Utwórz środowisko wirtualne:

```bash
python -m venv .venv
```

Aktywacja środowiska w systemie Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Aktywacja środowiska w systemie Linux lub macOS:

```bash
source .venv/bin/activate
```

Zaktualizuj pip:

```bash
python -m pip install --upgrade pip
```

## 5. Lokalne uruchomienie dashboardu

Zainstaluj zależności:

```bash
python -m pip install -r dashboard/requirements.txt
```

Sprawdź spójność zależności:

```bash
python -m pip check
```

Uruchom Streamlit z głównego katalogu repozytorium:

```bash
python -m streamlit run dashboard/app.py
```

Otwórz aplikację w przeglądarce:

http://localhost:8501

### Zbiór danych dashboardu

| Właściwość | Wartość |
|---|---|
| Sezony | 2021–2025 |
| Początkowa liczba rekordów | 2 278 |
| Liczba kolumn | 38 |
| Format | Parquet |
| Źródło | Widok analityczny Gold |
| Odświeżanie | Ręczny eksport snapshotu |

Dane i metadane znajdują się bezpośrednio w repozytorium:

- `dashboard/data/race_results.parquet`
- `dashboard/data/metadata.json`

Nie są wymagane dane uwierzytelniające Azure, połączenie z Databricks ani zapytania do zewnętrznego API.

Więcej informacji znajduje się w [dokumentacji dashboardu](../../dashboard/README.md).

## 6. Uruchomienie testów automatycznych

Sprawdź wersje Python i Java:

```bash
python --version
java -version
```

Zainstaluj zależności deweloperskie i dashboardu:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r dashboard/requirements.txt
```

Sprawdź spójność zależności:

```bash
python -m pip check
```

Uruchom wszystkie testy:

```bash
python -m pytest -q
```

Zestaw testów MVP zawiera 57 testów:

| Zestaw testów | Liczba |
|---|---:|
| Transformacje PySpark i jakość danych | 21 |
| Dashboard | 36 |
| Łącznie | 57 |

Uruchomienie wyłącznie testów pipeline'u:

```bash
python -m pytest tests -v
```

Uruchomienie wyłącznie testów dashboardu:

```bash
python -m pytest dashboard/tests -v
```

Testy automatyczne nie wymagają danych uwierzytelniających Azure.

CI wykorzystuje Python 3.12 oraz Java 17.

Podczas lokalnego testowania PySpark zaobserwowano ostrzeżenie dotyczące kompatybilności Pandas. Pomyślne wykonanie testów nie gwarantuje zgodności wszystkich operacji Spark zależnych od Pandas.

## 7. Konfiguracja infrastruktury Azure

Utwórz i skonfiguruj wymagane zasoby:

1. Azure Resource Group.
2. Konto ADLS Gen2 z włączoną hierarchiczną przestrzenią nazw.
3. Prywatne kontenery Bronze, Silver i Gold.
4. Azure Data Factory V2.
5. Azure Databricks Premium z obsługą Serverless.
6. Databricks Access Connector.
7. Budżet Azure i alerty kosztowe.

Skonfiguruj Managed Identity oraz uprawnienia Azure RBAC o ograniczonym zakresie.

Utwórz poświadczenie dostępu do magazynu danych oraz external locations w Unity Catalog.

Utwórz katalog `f1_lakehouse` i wymagane schematy:

- `bronze`
- `silver`
- `gold`
- `analytics`

Szczegółowa konfiguracja pierwotnego środowiska i model uprawnień znajdują się w dokumencie [Azure Environment Setup](../azure_setup.md).

Nazwy zasobów, regiony i identyfikatory należy dostosować do środowiska docelowego.

## 8. Konfiguracja Azure Data Factory

Definicje zasobów ADF są wersjonowane w katalogu:

`adf/`

Skonfiguruj integrację z GitHubem oraz linked services odpowiednie dla środowiska:

- `ls_http_jolpica`
- `ls_adls_gen2_f1`
- `ls_databricks_f1`

Zweryfikuj połączenia z magazynem danych i API.

Sprawdź pipeline'y:

- `pl_ingest_jolpica_page`
- `pl_ingest_jolpica_season`
- `pl_ingest_jolpica_all_seasons`
- `pl_f1_end_to_end`

Przed opublikowaniem konfiguracji zaktualizuj odwołania zależne od środowiska.

Zobacz [Bronze Data Ingestion](../bronze_ingestion.md).

## 9. Konfiguracja Azure Databricks

Sklonuj repozytorium GitHub do Databricks Git folder.

Zweryfikuj i dostosuj ścieżki magazynu danych oraz konfigurację katalogu do środowiska docelowego.

Uruchom notebook walidujący środowisko:

`notebooks/00_environment_validation.py`

Skonfiguruj Databricks Job na podstawie pliku:

`databricks/jobs/job_f1_lakehouse.json`

Zastąp znaczniki ścieżek odpowiednimi wartościami:

- `<WORKSPACE_NOTEBOOK_ROOT>`
- `<WORKSPACE_GIT_ROOT>`

Skonfiguruj zadania zgodnie z kolejnością zależności:

| Zadanie | Plik źródłowy |
|---|---|
| validate_bronze | notebooks/01_bronze_validation.py |
| bronze_to_silver | notebooks/02_bronze_to_silver.py |
| silver_to_gold | notebooks/03_silver_to_gold.py |
| deploy_analytics | sql/04_sql_business_analytics.sql |

W razie potrzeby zaimportuj plik SQL jako notebook SQL w Databricks, zgodnie z konfiguracją zadania.

Skonfiguruj tożsamość wykonującą Job i nadaj Managed Identity usługi ADF wymagane uprawnienia.

Zaktualizuj identyfikator Databricks Job w głównym pipeline ADF.

## 10. Uruchomienie pipeline'u End-to-End

Otwórz opublikowany pipeline Azure Data Factory:

`pl_f1_end_to_end`

Uruchom pełne ładowanie danych historycznych, przekazując parametr seasons:

```json
["2021", "2022", "2023", "2024", "2025"]
```

Monitoruj wykonanie za pomocą Azure Data Factory Monitor oraz Databricks Job Runs.

Pipeline wykonuje następujące operacje:

1. Walidacja parametrów wejściowych.
2. Pobieranie danych historycznych.
3. Walidacja warstwy Bronze.
4. Transformacja warstwy Silver.
5. Budowa modelu wymiarowego Gold.
6. Wdrożenie widoków analitycznych SQL.

Możliwe jest również odświeżenie wybranego sezonu:

```json
["2025"]
```

Pozostałe sezony historyczne muszą już znajdować się w warstwie Bronze.

Transformacje Silver i Gold nadal przebudowują kompletny zbiór historyczny.

## 11. Walidacja wyników

Uruchom notebook walidacyjny:

`notebooks/05_end_to_end_validation.py`

Pierwotny zweryfikowany zbiór danych zawierał:

| Zbiór danych | Liczba rekordów |
|---|---:|
| Pliki JSON Bronze | 25 |
| Wyniki wyścigów Silver | 2 278 |
| Kierowcy Gold | 35 |
| Konstruktorzy Gold | 12 |
| Tory Gold | 28 |
| Wyścigi Gold | 114 |
| Wyniki wyścigów Gold | 2 278 |

Dodatkowe wyniki walidacji:

- Zduplikowane klucze biznesowe: 0.
- Klucze obce bez dopasowania: 0.
- Widoki analityczne SQL: 6.
- Łączna liczba punktów Grand Prix: 11 540,50.

Podane wartości dotyczą pierwotnego zbioru historycznego i mogą ulec zmianie w przypadku korekt danych przez dostawcę API.

Zobacz [End-to-End Pipeline](../end_to_end_pipeline.md).

## 12. Odświeżenie snapshotu dashboardu

Po pomyślnej przebudowie warstwy Gold uruchom:

`notebooks/06_export_dashboard_snapshot.ipynb`

Notebook eksportuje dane z widoku:

`f1_lakehouse.analytics.vw_race_results`

Pliki wynikowe:

- `dashboard/data/race_results.parquet`
- `dashboard/data/metadata.json`

Zweryfikuj wyeksportowane pliki i przejrzyj zmiany przed zapisaniem ich w repozytorium GitHub.

Pobierz zaktualizowany snapshot do lokalnego repozytorium i ponownie uruchom dashboard.

Eksport snapshotu jest operacją ręczną, niezależną od głównego pipeline'u ADF.

## 13. Rozwiązywanie problemów

| Problem | Sugerowane rozwiązanie |
|---|---|
| Polecenie Python niedostępne | Sprawdź instalację Python i zmienną PATH |
| Brak pakietu Python | Zainstaluj zależności w aktywnym środowisku wirtualnym |
| Błąd inicjalizacji Spark | Sprawdź Java 17 oraz JAVA_HOME |
| Brak snapshotu | Sprawdź katalog dashboard/data |
| ADF HTTP 403 | Zweryfikuj Managed Identity i uprawnienia RBAC kontenera |
| Brak dostępu Databricks | Sprawdź uprawnienia workspace, Unity Catalog i Job |
| Błąd walidacji pipeline'u | Przeanalizuj logi ADF i Databricks |
| Niedostępny region Azure | Wybierz region obsługujący wymaganą usługę |

## 14. Bezpieczeństwo i zarządzanie kosztami

- Nie zapisuj haseł, tokenów ani kluczy konta magazynu w repozytorium.
- Wykorzystuj Managed Identity i uprawnienia o ograniczonym zakresie.
- Utrzymuj prywatne kontenery danych.
- Skonfiguruj alerty budżetowe Azure.
- Uruchamiaj przetwarzanie chmurowe tylko wtedy, gdy jest potrzebne.
- Po zakończeniu testów zweryfikuj koszty zasobów i przechowywania danych.

Alerty budżetowe Azure nie zatrzymują automatycznie naliczania kosztów.

Lokalny dashboard jest preferowaną formą demonstracji, gdy dostęp do chmury nie jest potrzebny.

## 15. Ograniczenia odtwarzalności

Lokalny dashboard i testy automatyczne można eksplorować niezależnie od Azure.

Pełne środowisko chmurowe wymaga ręcznej konfiguracji infrastruktury, tożsamości, uprawnień i ścieżek zależnych od workspace.

Automatyczne tworzenie infrastruktury i wdrażanie pozostają poza zakresem MVP.

Pierwotne środowisko Azure zostało zweryfikowane podczas prac deweloperskich. Pełne wdrożenie w niezależnym środowisku Azure nie zostało osobno przetestowane.

Korekty danych historycznych, aktualizacje zależności i dostępność usług Azure mogą wpływać na odtwarzalność projektu.

## 16. Powiązana dokumentacja

- [Architektura rozwiązania](architecture.md)
- [Konfiguracja Azure](../azure_setup.md)
- [Źródło danych](../data_source.md)
- [Pipeline End-to-End](../end_to_end_pipeline.md)
- [Jakość danych i CI](../data_quality_and_ci.md)
- [Dokumentacja dashboardu](../../dashboard/README.md)
- [Główny README](../../README.md)