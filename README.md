# 🗺️ POI2POL — Conversor CSV ➔ Shapefile (Polígonos)

O **POI2POL** é uma ferramenta web simplificada, desenvolvida em Python com Streamlit, projetada para converter coordenadas de pontos (POIs) listadas em arquivos CSV diretamente para arquivos Shapefile (.shp) de polígonos.

Esta ferramenta foi pensada especialmente para fluxos de trabalho que exigem rapidez na delimitação de áreas, como na fiscalização e proteção do patrimônio arqueológico.

## 🚀 Funcionalidades
* **Conversão Automática:** Transforma listas de coordenadas (X, Y) em polígonos fechados.
* **Projeção Nativa:** Configurado para **WGS 84 / UTM zone 23S (EPSG:32723)**.
* **Exportação Completa:** Gera um arquivo ZIP contendo todos os componentes do Shapefile (`.shp`, `.shx`, `.dbf`, `.prj`).
* **Validação:** Avisa se um polígono não possui o número mínimo de pontos (3) para ser formado.

## 📋 Como usar
1. Prepare seu arquivo CSV com as colunas: `nome`, `x`, `y`.
2. Faça o upload no aplicativo.
3. Visualize o preview dos dados e o resumo do processamento.
4. Clique em **Download ZIP com Shapefile**.

## 🛠️ Requisitos Técnicos
As dependências do projeto são:
* `streamlit`
* `pandas`
* `geopandas`
* `shapely`

Para rodar localmente:
```bash
pip install -r requirements.txt
streamlit run app.py# poi2pol
App no streamlint para conversão de malha de pontos csv em polígonos
