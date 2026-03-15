# 🗺️ POI2POL — Conversor e Extrator Geoespacial

O **POI2POL** é uma ferramenta web robusta desenvolvida em Python com Streamlit, projetada para facilitar o manejo de dados espaciais. Originalmente criado para converter coordenadas de pontos em polígonos, o app agora conta com um extrator de vértices, otimizando fluxos de trabalho na fiscalização e proteção do patrimônio arqueológico e histórico.

## 🚀 Funcionalidades Principais

### 1. 📍 CSV para Polígono (POI2POL)

* **Conversão Automática:** Transforma listas de coordenadas (X, Y) em polígonos fechados agrupados pela coluna `locacao`.
* **Suporte a Datums:** Escolha entre **WGS 84 (EPSG:32723)** ou **SIRGAS 2000 (EPSG:31983)**.
* **Validação Geométrica:** Verifica se os polígonos possuem pontos suficientes (mínimo 3) e detecta auto-interseções.
* **Exportação Completa:** Gera um arquivo ZIP contendo os componentes `.shp`, `.shx`, `.dbf` e `.prj`.

### 2. 📐 Extrator de Vértices

* **De Shapefile para CSV:** Carregue um ZIP de um Shapefile existente e extraia as coordenadas (X, Y, Z) de todos os seus vértices.
* **Preservação de Atributos:** Mantém os dados tabulares originais associados a cada vértice extraído.
* **Explosão de Geometria:** Suporta geometrias complexas e multi-partes.

---

## 📋 Como Usar

### Aba 1: Criar Polígonos

1. **Prepare o CSV:** O arquivo deve conter as colunas: `ponto`, `zona`, `x`, `y` e `locacao`.
2. **Upload:** Selecione o arquivo no painel correspondente.
3. **Configuração:** Escolha o Datum de saída.
4. **Download:** Baixe o Shapefile pronto para uso em GIS.

### Aba 2: Extrair Vértices

1. **Prepare o ZIP:** Compacte os arquivos do seu Shapefile (`.shp`, `.dbf`, etc) em um único `.zip`.
2. **Upload:** Envie o arquivo ZIP para o sistema.
3. **Visualização:** Confira a tabela de coordenadas gerada na tela.
4. **Exportação:** Baixe a lista de vértices em formato CSV.

---

## 🛠️ Requisitos Técnicos

As dependências principais do projeto são:

* `streamlit`
* `pandas`
* `geopandas`
* `shapely`
* `fiona`

**Para rodar localmente:**

```bash
pip install -r requirements.txt
streamlit run app.py

```
