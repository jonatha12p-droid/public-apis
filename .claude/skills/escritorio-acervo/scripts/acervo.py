#!/usr/bin/env python3
"""
acervo.py - acervo de pesquisas do escritorio virtual.

So biblioteca padrao do Python. Nenhuma chamada de LLM: busca, arquivamento,
validade, roteamento por palavras-chave e estatisticas rodam localmente
(custo: 0 tokens de modelo; o agente so paga pelo texto que le na saida).

Comandos:
  init        cria a estrutura de pastas e o indice
  buscar      procura no acervo (BM25 + cobertura de termos) e classifica
  ler         mostra resumo (padrao) ou o arquivo completo de uma pesquisa
  arquivar    guarda uma pesquisa com metadados e atualiza o indice
  vencidas    lista pesquisas fora da validade
  listar      lista o que existe no acervo
  reindexar   reconstroi o indice a partir dos arquivos .md
  rotear      escolhe o agente por palavras-chave (sem LLM)
  stats       taxa de reaproveitamento e economia estimada

Raiz do acervo: --raiz, ou variavel ESCRITORIO_ACERVO, ou ./escritorio/acervo
"""
import argparse
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

# Validade padrao (dias) por tipo de assunto. Ajuste ao seu uso.
VALIDADE_POR_TIPO = {
    "preco": 3,
    "noticia": 7,
    "mercado": 30,
    "legislacao": 60,
    "tecnologia": 90,
    "pesquisa-academica": 365,
    "conceito": 365,
}
VALIDADE_PADRAO = 90
LIMITE_RESUMO = 700  # caracteres; resumo curto e o que o diretor le
LIMIAR_FORTE = 0.70  # cobertura de termos da consulta para "forte"
LIMIAR_PARCIAL = 0.40

STOP = set(
    """a o as os um uma uns umas de do da dos das em no na nos nas por para com
    sem sobre entre e ou que como qual quais quem se ao aos ha sao foi ser mais
    the of and or to in on for with about is are what how which who an""".split()
)


# ---------------------------------------------------------------- utilidades
def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def tokens(s):
    out = []
    for t in re.findall(r"[a-z0-9]+", norm(s)):
        if t in STOP or len(t) < 2:
            continue
        if len(t) > 3 and t.endswith("s"):  # plural simples
            t = t[:-1]
        out.append(t)
    return out


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")
    return s[:60] or "sem-titulo"


def hoje_de(args):
    if getattr(args, "hoje", None):
        return date.fromisoformat(args.hoje)
    return date.today()


def raiz_de(args):
    r = args.raiz or os.environ.get("ESCRITORIO_ACERVO") or "escritorio/acervo"
    return Path(r).expanduser()


def carregar_indice(raiz):
    p = raiz / "index.json"
    if not p.exists():
        return {"versao": 1, "entradas": []}
    return json.loads(p.read_text(encoding="utf-8"))


def salvar_indice(raiz, idx):
    raiz.mkdir(parents=True, exist_ok=True)
    tmp = raiz / "index.json.tmp"
    tmp.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(raiz / "index.json")


def registrar(raiz, evento, **extra):
    try:
        raiz.mkdir(parents=True, exist_ok=True)
        linha = {"ts": datetime.now().isoformat(timespec="seconds"), "evento": evento}
        linha.update(extra)
        with open(raiz / "registro.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError:
        pass  # log nunca deve quebrar o fluxo


def ler_frontmatter(texto):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", texto, re.S)
    if not m:
        return {}, texto
    meta = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def valida_ate(e):
    return date.fromisoformat(e["criado"]) + timedelta(days=int(e["validade_dias"]))


def esta_vencida(e, hoje):
    return hoje > valida_ate(e)


# --------------------------------------------------------------------- busca
def pontuar(entradas, consulta, hoje):
    q = set(tokens(consulta))
    docs = []
    for e in entradas:
        toks = (
            tokens(e["titulo"]) * 3
            + tokens(" ".join(e.get("tags", []))) * 3
            + tokens(e.get("tipo", ""))
            + tokens(e["resumo"])
        )
        docs.append(toks)
    n = len(docs)
    avgdl = (sum(len(d) for d in docs) / n) if n else 1
    df = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    k1, b = 1.5, 0.75
    resultados = []
    for e, d in zip(entradas, docs):
        tf = Counter(d)
        dl = len(d) or 1
        score = 0.0
        for t in q:
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
        casados = sorted(t for t in q if t in tf)
        cov = len(casados) / len(q) if q else 0.0
        if cov >= LIMIAR_FORTE and len(casados) >= 2:
            nivel = "forte"
        elif cov >= LIMIAR_PARCIAL and casados:
            nivel = "parcial"
        else:
            continue
        resultados.append(
            {
                "e": e,
                "nivel": nivel,
                "cobertura": round(cov, 2),
                "bm25": round(score, 2),
                "fresca": not esta_vencida(e, hoje),
                "faltam": sorted(q - set(casados)),
            }
        )
    resultados.sort(
        key=lambda r: (r["nivel"] == "forte", r["fresca"], r["cobertura"], r["bm25"]),
        reverse=True,
    )
    return resultados


def cmd_buscar(a):
    raiz = raiz_de(a)
    hoje = hoje_de(a)
    idx = carregar_indice(raiz)
    entradas = idx["entradas"]
    if a.andar:
        entradas = [e for e in entradas if e["andar"] == slugify(a.andar)]
    if a.tipo:
        entradas = [e for e in entradas if e.get("tipo") == a.tipo]
    res = pontuar(entradas, a.consulta, hoje)[: a.top]

    if not res:
        resultado = "MISS"
    else:
        r0 = res[0]
        if r0["nivel"] == "forte" and r0["fresca"]:
            resultado = "HIT"
        elif r0["nivel"] == "forte":
            resultado = "VENCIDA"
        else:
            resultado = "PARCIAL"

    print(f"RESULTADO: {resultado}")
    for i, r in enumerate(res, 1):
        e = r["e"]
        estado = "fresca" if r["fresca"] else "VENCIDA"
        print(f"{i}. [{r['nivel']}|{estado}] {e['id']}  cobertura={r['cobertura']} bm25={r['bm25']}")
        print(f"   titulo: {e['titulo']}")
        print(f"   resumo: {e['resumo']}")
        print(f"   arquivo: {raiz / e['caminho']}  (criado {e['criado']}, valido ate {valida_ate(e)})")

    if resultado == "HIT":
        print("ACAO: responda com o resumo; abra o arquivo completo so se o resumo nao bastar.")
    elif resultado == "VENCIDA":
        print("ACAO: atualizacao incremental - pesquise so o que mudou desde a data de criacao.")
    elif resultado == "PARCIAL":
        faltam = ", ".join(res[0]["faltam"]) or "-"
        print(f"ACAO: pesquise so a lacuna. Termos nao cobertos: {faltam}")
    else:
        print("ACAO: pesquisa nova (nivel padrao ou profundo; ver references/politica-pesquisa.md).")

    if not a.sem_log:
        registrar(raiz, resultado, consulta=a.consulta, andar=a.andar or "*")


# ------------------------------------------------------------ ler / listar
def achar(idx, ident):
    exatos = [e for e in idx["entradas"] if e["id"] == ident]
    if exatos:
        return exatos[0]
    sufixo = [e for e in idx["entradas"] if e["id"].endswith("/" + ident) or e["id"].endswith(ident)]
    return sufixo[0] if len(sufixo) == 1 else None


def cmd_ler(a):
    raiz = raiz_de(a)
    idx = carregar_indice(raiz)
    e = achar(idx, a.id)
    if not e:
        sys.exit(f"nao encontrei '{a.id}'. Use: acervo.py listar")
    print(f"id: {e['id']}\ntitulo: {e['titulo']}\ncriado: {e['criado']}  valido ate: {valida_ate(e)}")
    print(f"tags: {', '.join(e.get('tags', []))}\nresumo: {e['resumo']}")
    print(f"arquivo: {raiz / e['caminho']}")
    if a.completo:
        _, corpo = ler_frontmatter((raiz / e["caminho"]).read_text(encoding="utf-8"))
        print("\n" + corpo.strip())


def cmd_listar(a):
    raiz = raiz_de(a)
    hoje = hoje_de(a)
    ents = carregar_indice(raiz)["entradas"]
    if a.andar:
        ents = [e for e in ents if e["andar"] == slugify(a.andar)]
    ents.sort(key=lambda e: e["criado"], reverse=True)
    for e in ents[: a.limite]:
        estado = "VENCIDA" if esta_vencida(e, hoje) else "ok"
        print(f"{e['id']}  [{e.get('tipo','-')}]  {e['criado']}  {estado}")
    print(f"({len(ents)} no total)")


def cmd_vencidas(a):
    raiz = raiz_de(a)
    hoje = hoje_de(a)
    ents = carregar_indice(raiz)["entradas"]
    if a.andar:
        ents = [e for e in ents if e["andar"] == slugify(a.andar)]
    venc = [e for e in ents if esta_vencida(e, hoje)]
    for e in sorted(venc, key=valida_ate):
        print(f"{e['id']}  venceu em {valida_ate(e)}")
    print(f"({len(venc)} vencidas de {len(ents)})")


# ------------------------------------------------------------------ arquivar
def cmd_arquivar(a):
    raiz = raiz_de(a)
    hoje = hoje_de(a)
    src = Path(a.arquivo)
    if not src.is_file():
        sys.exit(f"arquivo nao encontrado: {src}")
    resumo = " ".join(a.resumo.split())
    if len(resumo) > LIMITE_RESUMO:
        sys.exit(f"resumo com {len(resumo)} caracteres; maximo {LIMITE_RESUMO}. Resuma mais.")
    if len(resumo) < 40:
        sys.exit("resumo curto demais (minimo 40 caracteres): ele e o que o diretor vai ler.")
    _, corpo = ler_frontmatter(src.read_text(encoding="utf-8"))
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    validade = a.validade_dias if a.validade_dias is not None else VALIDADE_POR_TIPO.get(a.tipo, VALIDADE_PADRAO)
    andar, slug = slugify(a.andar), slugify(a.titulo)
    eid = f"{andar}/{slug}"
    pasta = raiz / andar
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{slug}.md"

    idx = carregar_indice(raiz)
    substituiu = False
    if destino.exists():
        hist = pasta / "_historico"
        hist.mkdir(exist_ok=True)
        destino.replace(hist / f"{slug}-{datetime.now():%Y%m%d-%H%M%S}.md")
        substituiu = True
    idx["entradas"] = [e for e in idx["entradas"] if e["id"] != eid]

    fontes = [f.strip() for f in (a.fontes or "").split("|") if f.strip()]
    meta = [
        "---",
        f"id: {eid}",
        f"titulo: {a.titulo}",
        f"andar: {andar}",
        f"tipo: {a.tipo}",
        f"tags: {', '.join(tags)}",
        f"criado: {hoje.isoformat()}",
        f"validade_dias: {validade}",
        f"nota: {a.nota if a.nota is not None else ''}",
        f"fontes: {' | '.join(fontes)}",
        f"resumo: {resumo}",
        "---",
        "",
    ]
    destino.write_text("\n".join(meta) + corpo.lstrip("\n"), encoding="utf-8")

    entrada = {
        "id": eid,
        "andar": andar,
        "titulo": a.titulo,
        "tipo": a.tipo,
        "tags": tags,
        "resumo": resumo,
        "criado": hoje.isoformat(),
        "validade_dias": int(validade),
        "nota": a.nota,
        "fontes": fontes,
        "palavras": len(corpo.split()),
        "caminho": f"{andar}/{slug}.md",
    }
    idx["entradas"].append(entrada)
    salvar_indice(raiz, idx)
    registrar(raiz, "ARQUIVADO", id=eid, substituiu=substituiu)
    print(f"ARQUIVADO: {eid}  (valido ate {hoje + timedelta(days=int(validade))}"
          f"{', versao anterior movida para _historico' if substituiu else ''})")


def cmd_reindexar(a):
    raiz = raiz_de(a)
    entradas = []
    for arq in sorted(raiz.glob("*/*.md")):
        if arq.parent.name.startswith("_"):
            continue
        meta, corpo = ler_frontmatter(arq.read_text(encoding="utf-8"))
        if not meta.get("titulo") or not meta.get("criado"):
            print(f"ignorado (sem frontmatter valido): {arq}")
            continue
        entradas.append(
            {
                "id": meta.get("id") or f"{arq.parent.name}/{arq.stem}",
                "andar": arq.parent.name,
                "titulo": meta["titulo"],
                "tipo": meta.get("tipo", ""),
                "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
                "resumo": meta.get("resumo", ""),
                "criado": meta["criado"],
                "validade_dias": int(meta.get("validade_dias") or VALIDADE_PADRAO),
                "nota": int(meta["nota"]) if meta.get("nota", "").isdigit() else None,
                "fontes": [f.strip() for f in meta.get("fontes", "").split("|") if f.strip()],
                "palavras": len(corpo.split()),
                "caminho": f"{arq.parent.name}/{arq.name}",
            }
        )
    salvar_indice(raiz, {"versao": 1, "entradas": entradas})
    print(f"indice reconstruido: {len(entradas)} pesquisas")


def cmd_init(a):
    raiz = raiz_de(a)
    for andar in [x for x in (a.andares or "").split(",") if x.strip()]:
        (raiz / slugify(andar)).mkdir(parents=True, exist_ok=True)
    if not (raiz / "index.json").exists():
        salvar_indice(raiz, {"versao": 1, "entradas": []})
    print(f"acervo pronto em {raiz}")


# ------------------------------------------------------------------- rotear
def cmd_rotear(a):
    raiz = raiz_de(a)
    tabela = json.loads(Path(a.tabela).read_text(encoding="utf-8"))
    q = set(tokens(a.pedido))
    pont = []
    for ag in tabela["agentes"]:
        palavras = {t for p in ag.get("palavras", []) for t in tokens(p)}
        casadas = sorted(q & palavras)
        pont.append((len(casadas), ag["nome"], ag.get("andar", ""), casadas))
    pont.sort(key=lambda x: (-x[0], x[1]))
    melhor = pont[0] if pont else None
    segundo = pont[1] if len(pont) > 1 else None
    if melhor and melhor[0] >= a.minimo and (segundo is None or melhor[0] - segundo[0] >= a.margem):
        print(f"ROTA: {melhor[1]}  (andar {melhor[2]}; termos: {', '.join(melhor[3])})")
        registrar(raiz, "ROTA_REGRA", agente=melhor[1])
        return
    candidatos = [p for p in pont if p[0] > 0][:3]
    if candidatos:
        print("AMBIGUO: decida entre os candidatos abaixo (use o modelo menor, so com este trecho)")
        for c in candidatos:
            print(f"  - {c[1]} (andar {c[2]}; termos: {', '.join(c[3])})")
        registrar(raiz, "ROTA_AMBIGUA")
    else:
        padrao = tabela.get("padrao", "")
        print(f"SEM_CANDIDATO: use o agente padrao '{padrao}' ou pergunte ao solicitante")
        registrar(raiz, "ROTA_SEM_CANDIDATO")


# -------------------------------------------------------------------- stats
def cmd_stats(a):
    raiz = raiz_de(a)
    log = raiz / "registro.jsonl"
    if not log.exists():
        print("sem registros ainda")
        return
    c = Counter()
    for linha in log.read_text(encoding="utf-8").splitlines():
        try:
            c[json.loads(linha)["evento"]] += 1
        except (ValueError, KeyError):
            continue
    buscas = sum(c[k] for k in ("HIT", "PARCIAL", "VENCIDA", "MISS"))
    print(f"buscas: {buscas}  HIT={c['HIT']}  PARCIAL={c['PARCIAL']}  VENCIDA={c['VENCIDA']}  MISS={c['MISS']}")
    if buscas:
        print(f"taxa de reaproveitamento total (HIT): {c['HIT'] / buscas:.0%}")
        print(f"reaproveitamento parcial/incremental: {(c['PARCIAL'] + c['VENCIDA']) / buscas:.0%}")
    rotas = c["ROTA_REGRA"] + c["ROTA_AMBIGUA"] + c["ROTA_SEM_CANDIDATO"]
    if rotas:
        print(f"roteamentos resolvidos so por regra (sem LLM): {c['ROTA_REGRA'] / rotas:.0%} de {rotas}")
    print(f"pesquisas arquivadas: {c['ARQUIVADO']}")
    economia = (
        c["HIT"] * (a.custo_pesquisa - a.custo_hit)
        + c["PARCIAL"] * 0.5 * a.custo_pesquisa
        + c["VENCIDA"] * 0.3 * a.custo_pesquisa
    )
    print(
        f"economia ESTIMADA: ~{int(economia):,} tokens "
        f"(premissas: pesquisa nova {a.custo_pesquisa:,}, reaproveitar {a.custo_hit:,}; "
        "parcial economiza 50%, vencida 30%). Meca o seu custo real e ajuste os parametros."
    )


# --------------------------------------------------------------------- main
def main():
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--raiz", help="pasta do acervo (padrao: $ESCRITORIO_ACERVO ou ./escritorio/acervo)")
    comum.add_argument("--hoje", help="data AAAA-MM-DD (para testes)")

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("init", parents=[comum])
    s.add_argument("--andares", help="lista separada por virgula, ex: pesquisa,desenvolvimento")
    s.set_defaults(f=cmd_init)

    s = sp.add_parser("buscar", parents=[comum])
    s.add_argument("consulta")
    s.add_argument("--andar")
    s.add_argument("--tipo")
    s.add_argument("--top", type=int, default=3)
    s.add_argument("--sem-log", action="store_true")
    s.set_defaults(f=cmd_buscar)

    s = sp.add_parser("ler", parents=[comum])
    s.add_argument("id")
    s.add_argument("--completo", action="store_true")
    s.set_defaults(f=cmd_ler)

    s = sp.add_parser("arquivar", parents=[comum])
    s.add_argument("--arquivo", required=True)
    s.add_argument("--andar", required=True)
    s.add_argument("--titulo", required=True)
    s.add_argument("--tipo", default="conceito", help=f"um de: {', '.join(VALIDADE_POR_TIPO)}")
    s.add_argument("--tags", default="")
    s.add_argument("--resumo", required=True)
    s.add_argument("--fontes", default="", help="URLs separadas por ' | '")
    s.add_argument("--validade-dias", type=int)
    s.add_argument("--nota", type=int, choices=range(1, 6), help="nota do diretor (1-5)")
    s.set_defaults(f=cmd_arquivar)

    s = sp.add_parser("vencidas", parents=[comum])
    s.add_argument("--andar")
    s.set_defaults(f=cmd_vencidas)

    s = sp.add_parser("listar", parents=[comum])
    s.add_argument("--andar")
    s.add_argument("--limite", type=int, default=30)
    s.set_defaults(f=cmd_listar)

    s = sp.add_parser("reindexar", parents=[comum])
    s.set_defaults(f=cmd_reindexar)

    s = sp.add_parser("rotear", parents=[comum])
    s.add_argument("pedido")
    s.add_argument("--tabela", required=True, help="JSON com agentes e palavras-chave")
    s.add_argument("--minimo", type=int, default=2, help="termos minimos casados")
    s.add_argument("--margem", type=int, default=1, help="vantagem minima sobre o 2o colocado")
    s.set_defaults(f=cmd_rotear)

    s = sp.add_parser("stats", parents=[comum])
    s.add_argument("--custo-pesquisa", type=int, default=120000, help="tokens medios de uma pesquisa nova")
    s.add_argument("--custo-hit", type=int, default=6000, help="tokens medios para reaproveitar")
    s.set_defaults(f=cmd_stats)

    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
