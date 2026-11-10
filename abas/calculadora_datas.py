from datetime import date, timedelta

import streamlit as st
from dateutil.relativedelta import relativedelta

DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]
DATA_MIN, DATA_MAX = date(1900, 1, 1), date(2200, 12, 31)


def _fmt(d: date) -> str:
    return f"{d.strftime('%d/%m/%Y')} ({DIAS_SEMANA[d.weekday()]})"


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _periodo_entre_datas():
    c1, c2 = st.columns(2)
    with c1:
        inicio = st.date_input("Data inicial:", value=date.today(), min_value=DATA_MIN,
                               max_value=DATA_MAX, format="DD/MM/YYYY", key="dt_ini")
    with c2:
        fim = st.date_input("Data final:", value=date.today(), min_value=DATA_MIN,
                            max_value=DATA_MAX, format="DD/MM/YYYY", key="dt_fim")
    inclusivo = st.checkbox("Contar também o dia final (inclusive)", value=False, key="dt_incl")

    if st.button("📆 Calcular período", key="btn_periodo"):
        if fim < inicio:
            inicio, fim = fim, inicio
            st.info("A data final era anterior à inicial; as datas foram invertidas para o cálculo.")

        fim_calc = fim + timedelta(days=1) if inclusivo else fim
        rd = relativedelta(fim_calc, inicio)
        total_dias = (fim_calc - inicio).days

        st.success("✅ Período calculado!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Anos", rd.years)
        m2.metric("Meses", rd.months)
        m3.metric("Dias", rd.days)

        st.write(f"**{_plural(rd.years, 'ano', 'anos')}, {_plural(rd.months, 'mês', 'meses')} "
                 f"e {_plural(rd.days, 'dia', 'dias')}**")
        semanas, resto = divmod(total_dias, 7)
        st.write(f"Total: **{total_dias:,}** dias".replace(",", ".")
                 + f" (≈ {_plural(semanas, 'semana', 'semanas')} e {_plural(resto, 'dia', 'dias')})")
        st.caption(f"De {_fmt(inicio)} até {_fmt(fim)}" + (" (inclusive)" if inclusivo else ""))


def _somar_subtrair():
    c1, c2 = st.columns(2)
    with c1:
        base = st.date_input("Data de referência:", value=date.today(), min_value=DATA_MIN,
                             max_value=DATA_MAX, format="DD/MM/YYYY", key="dt_base")
    with c2:
        operacao = st.radio("Operação:", ["Somar (a mais)", "Subtrair (a menos)"],
                            horizontal=True, key="dt_op")

    c3, c4, c5 = st.columns(3)
    with c3:
        anos = st.number_input("Anos:", min_value=0, value=0, step=1, key="dt_anos")
    with c4:
        meses = st.number_input("Meses:", min_value=0, value=0, step=1, key="dt_meses")
    with c5:
        dias = st.number_input("Dias:", min_value=0, value=0, step=1, key="dt_dias")

    if st.button("📆 Calcular data", key="btn_somar"):
        delta = relativedelta(years=int(anos), months=int(meses), days=int(dias))
        try:
            resultado = base + delta if operacao.startswith("Somar") else base - delta
        except (OverflowError, ValueError):
            st.error("O resultado ficou fora do intervalo de datas suportado.")
            return

        sinal = "+" if operacao.startswith("Somar") else "−"
        st.success("✅ Data calculada!")
        st.metric("Data resultante", resultado.strftime("%d/%m/%Y"))
        st.write(f"**{_fmt(resultado)}**")
        st.caption(f"{_fmt(base)} {sinal} {_plural(int(anos), 'ano', 'anos')}, "
                   f"{_plural(int(meses), 'mês', 'meses')} e {_plural(int(dias), 'dia', 'dias')}. "
                   f"Diferença total: {abs((resultado - base).days)} dias.")
        st.caption("Ao somar meses, se o dia não existir no mês final (ex.: 31/01 + 1 mês), "
                   "usa-se o último dia do mês (28 ou 29/02).")


def render():
    st.header("Calculadora de Prazos")
    modo = st.radio("O que você quer calcular?",
                    ["Período entre duas datas", "Somar ou subtrair tempo de uma data"],
                    horizontal=True, key="dt_modo")
    if modo.startswith("Período"):
        _periodo_entre_datas()
    else:
        _somar_subtrair()
