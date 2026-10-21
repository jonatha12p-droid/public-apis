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
  pedir       grava um pedido de um andar para outro
  triar       roteia + busca um pedido e monta a decisao (no HIT ja responde)
  responder   grava a resposta no andar de origem e fecha o pedido
  checar      checklist mecanico de curadoria de um relatorio
  auditar     revisa a qualidade do acervo (sem LLM)
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
    "ia": 30,
    "redes-sociais": 30,
    "ferramenta": 60,
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
# Trechos do resumo que a propria pesquisa marca como incertos. Termo da
# consulta que so aparece neles nao conta para HIT (evita HIT falso).
MARCAS_INCERTEZA = ("incerteza", "nao verificad", "lacuna", "inferencia", "nao testad")


def separar_resumo(resumo):
    """Divide o resumo em (parte firme, parte incerta) por frase."""
    firme, incerta, apos_rotulo = [], [], False
    for frase in re.split(r"(?<=[.;])\s+", resumo):
        n = norm(frase)
        if n.lstrip().startswith("incerteza"):
            apos_rotulo = True
        (incerta if apos_rotulo or any(m in n for m in MARCAS_INCERTEZA) else firme).append(frase)
    return " ".join(firme), " ".join(incerta)


def pontuar(entradas, consulta, hoje):
    q = set(tokens(consulta))
    docs, firmes = [], []
    for e in entradas:
        resumo_firme, _ = separar_resumo(e["resumo"])
        base = (
            tokens(e["titulo"]) * 3
            + tokens(" ".join(e.get("tags", []))) * 3
            + tokens(e.get("tipo", ""))
        )
        docs.append(base + tokens(e["resumo"]))
        firmes.append(set(base + tokens(resumo_firme)))
    n = len(docs)
    avgdl = (sum(len(d) for d in docs) / n) if n else 1
    df = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    k1, b = 1.5, 0.75
    resultados = []
    for e, d, firme in zip(entradas, docs, firmes):
        tf = Counter(d)
        dl = len(d) or 1
        score = 0.0
        for t in q:
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
        casados = sorted(t for t in q if t in tf)
        cov = len(casados) / len(q) if q else 0.0
        incertos = sorted(t for t in casados if t not in firme)
        cov_firme = (len(casados) - len(incertos)) / len(q) if q else 0.0
        if cov >= LIMIAR_FORTE and len(casados) >= 2 and cov_firme >= LIMIAR_FORTE:
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
                "incertos": incertos,
            }
        )
    resultados.sort(
        key=lambda r: (r["nivel"] == "forte", r["fresca"], r["cobertura"], r["bm25"]),
        reverse=True,
    )
    return resultados


def classificar(res):
    if not res:
        return "MISS"
    r0 = res[0]
    if r0["nivel"] == "forte":
        return "HIT" if r0["fresca"] else "VENCIDA"
    return "PARCIAL"


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
    resultado = classificar(res)

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
        if res[0]["incertos"]:
            print(f"      Termos que a pesquisa marca como incertos: {', '.join(res[0]['incertos'])}")
    else:
        print("ACAO: pesquisa nova (nivel padrao ou profundo; ver references/politica-pesquisa.md).")

    if not a.sem_log:
        registrar(raiz, resultado, consulta=a.consulta, andar=a.andar or "*",
                  alvo=res[0]["e"]["id"] if res else None)


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
TABELA_PADRAO = Path(__file__).resolve().parent.parent / "references" / "roteamento.json"


def avaliar_rota(tabela, texto, minimo=2, margem=1):
    """Devolve ("ROTA", [melhor]) ou ("AMBIGUO", ate 3 candidatos) ou ("SEM_CANDIDATO", [])."""
    q = set(tokens(texto))
    pont = []
    for ag in tabela["agentes"]:
        palavras = {t for p in ag.get("palavras", []) for t in tokens(p)}
        casadas = sorted(q & palavras)
        pont.append((len(casadas), ag["nome"], ag.get("andar", ""), casadas))
    pont.sort(key=lambda x: (-x[0], x[1]))
    melhor = pont[0] if pont else None
    segundo = pont[1] if len(pont) > 1 else None
    if melhor and melhor[0] >= minimo and (segundo is None or melhor[0] - segundo[0] >= margem):
        return "ROTA", [melhor]
    candidatos = [p for p in pont if p[0] > 0][:3]
    return ("AMBIGUO" if candidatos else "SEM_CANDIDATO"), candidatos


def cmd_rotear(a):
    raiz = raiz_de(a)
    tabela = json.loads(Path(a.tabela).read_text(encoding="utf-8"))
    tipo, candidatos = avaliar_rota(tabela, a.pedido, a.minimo, a.margem)
    if tipo == "ROTA":
        melhor = candidatos[0]
        print(f"ROTA: {melhor[1]}  (andar {melhor[2]}; termos: {', '.join(melhor[3])})")
        registrar(raiz, "ROTA_REGRA", agente=melhor[1])
        return
    if candidatos:
        print("AMBIGUO: decida entre os candidatos abaixo (use o modelo menor, so com este trecho)")
        for c in candidatos:
            print(f"  - {c[1]} (andar {c[2]}; termos: {', '.join(c[3])})")
        registrar(raiz, "ROTA_AMBIGUA")
    else:
        padrao = tabela.get("padrao", "")
        print(f"SEM_CANDIDATO: use o agente padrao '{padrao}' ou pergunte ao solicitante")
        registrar(raiz, "ROTA_SEM_CANDIDATO")


# ------------------------------------------- pedidos entre andares (sem LLM)
NIVEIS = ["rapida", "padrao", "profunda"]
MINIMO_FONTES = {"rapida": 3, "padrao": 8, "profunda": 15}


def escritorio_de(a):
    return Path(a.escritorio) if getattr(a, "escritorio", None) else raiz_de(a).parent


def secoes(corpo):
    """Mapa titulo normalizado -> texto. Titulos '#' e '##' abrem secao; '###' fica dentro."""
    out, atual = {}, None
    for linha in corpo.splitlines():
        m = re.match(r"^#{1,2}\s+(.*)", linha)
        if m:
            atual = norm(m.group(1)).strip()
            out[atual] = []
        elif atual is not None:
            out[atual].append(linha)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def secao(mapa, *nomes):
    for k, v in mapa.items():
        if any(k.startswith(n) for n in nomes):
            return v
    return ""


def atualizar_frontmatter(arq, **campos):
    texto = arq.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", texto, re.S)
    linhas = m.group(1).splitlines() if m else []
    resto = texto[m.end():] if m else texto
    for k, v in campos.items():
        nova = f"{k}: {v}"
        for i, l in enumerate(linhas):
            if l.split(":", 1)[0].strip() == k:
                linhas[i] = nova
                break
        else:
            linhas.append(nova)
    arq.write_text("---\n" + "\n".join(linhas) + "\n---\n" + resto.lstrip("\n"), encoding="utf-8")


def valor(meta, k, padrao=""):
    return (meta.get(k) or padrao).split("#")[0].strip()


def cmd_pedir(a):
    esc = escritorio_de(a)
    hoje = hoje_de(a)
    de, para = slugify(a.de), slugify(a.para)
    if a.nivel not in NIVEIS:
        sys.exit(f"nivel deve ser um de: {', '.join(NIVEIS)}")
    slug = slugify(a.titulo or a.palavras or a.pergunta)[:50].strip("-")
    q = set(tokens(a.pergunta))
    for resp in sorted((esc / de / "respostas").glob("*.md")):
        meta, corpo = ler_frontmatter(resp.read_text(encoding="utf-8"))
        ped = esc.parent / meta.get("pedido", "")
        if ped.is_file():
            _, cped = ler_frontmatter(ped.read_text(encoding="utf-8"))
            antiga = set(tokens(secao(secoes(cped), "pergunta")))
            if q and antiga and len(q & antiga) / len(q | antiga) >= 0.6:
                print(f"JA_RESPONDIDO: {resp.relative_to(esc.parent)}  (pergunta parecida; use essa resposta ou passe --forcar)")
                if not a.forcar:
                    return
    pasta = esc / para / "pedidos"
    pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"{hoje.isoformat()}-{slug}.md"
    n = 2
    while arq.exists():
        arq = pasta / f"{hoje.isoformat()}-{slug}-{n}.md"
        n += 1
    criterios = "\n".join(f"- {c}" for c in a.criterio) or "- <defina o criterio>"
    arq.write_text(
        f"---\nde: {de}\npara: {para}\nstatus: aberto\nnivel_sugerido: {a.nivel}\n"
        f"palavras: {a.palavras or ''}\ncriado: {hoje.isoformat()}\n---\n"
        f"# Pergunta\n{a.pergunta}\n\n# Para que serve\n{a.para_que or '-'}\n\n# Respondida quando\n{criterios}\n",
        encoding="utf-8",
    )
    registrar(raiz_de(a), "PEDIDO", de=de, para=para, arquivo=arq.name)
    print(f"PEDIDO: {arq.relative_to(esc.parent)}")
    print(f"PROXIMO: acervo.py triar {arq.relative_to(esc.parent)}")


def cmd_triar(a):
    raiz, hoje = raiz_de(a), hoje_de(a)
    ped = Path(a.pedido)
    if not ped.is_file():
        sys.exit(f"pedido nao encontrado: {ped}")
    meta, corpo = ler_frontmatter(ped.read_text(encoding="utf-8"))
    mapa = secoes(corpo)
    pergunta = secao(mapa, "pergunta")
    consulta = a.consulta or valor(meta, "palavras") or pergunta
    sugerido = valor(meta, "nivel_sugerido", "padrao")
    sugerido = sugerido if sugerido in NIVEIS else "padrao"

    tabela = json.loads(Path(a.tabela).read_text(encoding="utf-8"))
    rota, cands = avaliar_rota(tabela, consulta + " " + pergunta, a.minimo, a.margem)
    registrar(raiz, {"ROTA": "ROTA_REGRA", "AMBIGUO": "ROTA_AMBIGUA"}.get(rota, "ROTA_SEM_CANDIDATO"),
              agente=cands[0][1] if rota == "ROTA" else None)
    if rota == "ROTA":
        agente = cands[0][1]
    elif rota == "AMBIGUO":
        agente = "ESCOLHA entre " + " | ".join(f"{c[1]} ({', '.join(c[3])})" for c in cands)
    else:
        agente = tabela.get("padrao", "")

    res = pontuar(carregar_indice(raiz)["entradas"], consulta, hoje)[:3]
    resultado = classificar(res)
    registrar(raiz, resultado, consulta=consulta, andar="*", alvo=res[0]["e"]["id"] if res else None)

    if resultado == "MISS" and sugerido == "rapida" and not a.rapida_ok:
        nivel, nota_nivel = "padrao", " (subiu de rapida: MISS pede no minimo padrao; use --rapida-ok se for pergunta factual simples)"
    else:
        nivel, nota_nivel = sugerido, ""
    saida = (escritorio_de(a) / "pesquisa" / "rascunhos" / ped.name).relative_to(escritorio_de(a).parent)
    alvo = res[0]["e"]["id"] if res else ""
    atualizar_frontmatter(ped, triagem=resultado, alvo=alvo, agente=agente if rota != "AMBIGUO" else "",
                          nivel=nivel, saida=str(saida))

    print(f"TRIAGEM: {resultado}   (consulta: {consulta})")
    if res:
        r0 = res[0]
        print(f"ACERVO: {alvo}  [{r0['nivel']}|{'fresca' if r0['fresca'] else 'VENCIDA'}] cobertura={r0['cobertura']}")
        print(f"RESUMO: {r0['e']['resumo']}")
    if resultado == "HIT":
        if a.sem_resposta:
            print(f"PROXIMO: acervo.py responder {ped} --id {alvo}")
        else:
            responder(a, ped, alvo)
        return
    print("DECISAO:")
    print(f"  agente: {agente}")
    print(f"  nivel: {nivel}{nota_nivel}")
    if resultado == "PARCIAL":
        print(f"  escopo: so a lacuna; termos nao cobertos: {', '.join(res[0]['faltam']) or '-'}"
              + (f"; incertos na pesquisa existente: {', '.join(res[0]['incertos'])}" if res[0]["incertos"] else ""))
        print(f"  base: {alvo} (nao repetir o que ela ja cobre)")
    elif resultado == "VENCIDA":
        print(f"  escopo: atualizacao incremental desde {res[0]['e']['criado']}; base: {alvo}")
    else:
        print("  escopo: pesquisa nova completa")
    print(f"  pergunta: {' '.join(pergunta.split())}")
    print("  respondida quando:")
    for linha in secao(mapa, "respondida").splitlines():
        if linha.strip():
            print(f"    {linha.strip()}")
    print(f"  saida: {saida}")
    print(f"PROXIMO: acione o agente com este bloco; depois acervo.py checar {saida} --nivel {nivel}")


def responder(a, ped, ident=None, motivo=None):
    raiz, hoje, esc = raiz_de(a), hoje_de(a), escritorio_de(a)
    meta, _ = ler_frontmatter(ped.read_text(encoding="utf-8"))
    origem = slugify(valor(meta, "de", "pesquisa"))
    destino = esc / origem / "respostas" / ped.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    resultado = valor(meta, "triagem", "-")
    if motivo:
        corpo = f"# Resposta: pesquisa descartada\n\n## Motivo\n{motivo}\n"
        cab = {"resultado": resultado, "nota": "descartada"}
    else:
        e = achar(carregar_indice(raiz), ident)
        if not e:
            sys.exit(f"nao encontrei '{ident}' no acervo")
        corpo = (f"# Resposta: {e['titulo']}\n\n## Resumo\n{e['resumo']}\n\n## Caminho no acervo\n"
                 f"{(raiz / e['caminho'])}  (valido ate {valida_ate(e)})\n")
        cab = {"resultado": resultado, "nota": e.get("nota") or "-", "acervo": e["id"]}
    linhas = [f"pedido: {ped}", "de: pesquisa", f"para: {origem}"] + [f"{k}: {v}" for k, v in cab.items()] + [f"data: {hoje.isoformat()}"]
    destino.write_text("---\n" + "\n".join(linhas) + "\n---\n" + corpo, encoding="utf-8")
    atualizar_frontmatter(ped, status="respondido", resposta=str(destino))
    registrar(raiz, "RESPONDIDO", pedido=ped.name, resultado=resultado, descartado=bool(motivo))
    print(f"RESPONDIDO: {destino}  (pedido marcado como respondido)")


def cmd_responder(a):
    ped = Path(a.pedido)
    if not ped.is_file():
        sys.exit(f"pedido nao encontrado: {ped}")
    if bool(a.id) == bool(a.descartar):
        sys.exit("passe --id <pesquisa arquivada> ou --descartar \"motivo\" (um dos dois)")
    responder(a, ped, a.id, a.descartar)


def cmd_checar(a):
    arq = Path(a.relatorio)
    if not arq.is_file():
        sys.exit(f"relatorio nao encontrado: {arq}")
    _, corpo = ler_frontmatter(arq.read_text(encoding="utf-8"))
    mapa = secoes(corpo)
    achados = secao(mapa, "achado")
    contra = secao(mapa, "contraponto", "critica", "limitac")
    incert = secao(mapa, "incerteza", "lacuna")
    fontes = secao(mapa, "fonte", "referencia")
    angulos = len(re.findall(r"^###\s+", achados, re.M))
    entradas = [l for l in fontes.splitlines() if re.match(r"^\s*(\[\d+\]|[-*]|\d+\.)\s+\S", l)]
    urls = {u.rstrip(".,;") for l in entradas for u in re.findall(r"https?://[^\s)>\]]+", l)}
    dominios = {re.sub(r"^www\.", "", u.split("/")[2]) for u in urls}
    primarias = [l for l in entradas if re.search(r"primari|oficial", norm(l))]
    com_data = [l for l in entradas if re.search(r"\b(19|20)\d\d\b", l)]
    bullets = [l for l in achados.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]
    # sub-itens herdam a citacao do item de cima; interpretacao declarada nao precisa de fonte
    sem_fonte = [l.strip() for l in bullets
                 if not l[0].isspace() and not re.search(r"\[\d+", l) and "interpreta" not in norm(l)]
    num_nao_verif = [l.strip() for l in bullets if re.search(r"\d", l) and "nao verificad" in norm(l)]
    verif = len(re.findall(r"\[verificado\]", corpo, re.I))
    nao_verif = len(re.findall(r"\[n[aã]o verificado\]", corpo, re.I))
    minimo = MINIMO_FONTES.get(a.nivel, 8)

    itens = [
        ("3+ angulos em Achados (### )", angulos >= 3, f"{angulos} angulos"),
        (f"{minimo}+ fontes distintas", len(entradas) >= minimo, f"{len(entradas)} fontes listadas, {len(dominios)} dominios"),
        ("fontes primarias", bool(primarias), f"{len(primarias)} marcadas como primaria/oficial"),
        ("contraponto ou limitacoes", len(contra) >= 80, f"{len(contra)} caracteres"),
        ("incertezas e datas das fontes", len(incert) >= 40 and len(com_data) >= len(entradas) / 2 > 0,
         f"secao {len(incert)} caracteres; {len(com_data)}/{len(entradas)} fontes com ano"),
    ]
    pontos = sum(ok for _, ok, _ in itens)
    ajuste = -1 if (sem_fonte or num_nao_verif) else 0
    # passe de verificacao: a maioria das afirmacoes marcadas precisa estar verificada
    pouca_verificacao = nao_verif > verif
    if pouca_verificacao:
        ajuste -= 1
    print(f"CHECAGEM: {arq}  (nivel {a.nivel})")
    for nome, ok, det in itens:
        print(f"  [{'x' if ok else ' '}] {nome}: {det}")
    print(f"  marcas: {verif} [verificado], {nao_verif} [nao verificado]")
    if sem_fonte:
        print(f"  ajuste -1: {len(sem_fonte)} item(ns) de Achados sem citacao [n], ex.: {sem_fonte[0][:100]}")
    if num_nao_verif:
        print(f"  ajuste -1: {len(num_nao_verif)} numero(s) marcados como nao verificados, ex.: {num_nao_verif[0][:100]}")
    if pouca_verificacao:
        print(f"  ajuste -1: mais afirmacoes [nao verificado] ({nao_verif}) que [verificado] ({verif}); "
              "o passe de verificacao nao foi feito (leia as fontes inteiras)")
    nota = max(1, pontos + ajuste)
    print(f"NOTA_PROVISORIA: {nota}  ({pontos} itens, ajuste {ajuste})")
    print("PARA_JULGAR (o script nao ve): profundidade real de cada angulo; se as afirmacoes centrais tem 2+ "
          "fontes independentes; se as fontes primarias existem de fato. Confirme ou corrija a nota.")


# ------------------------------------------------------------------ auditar
def cmd_auditar(a):
    raiz = raiz_de(a)
    hoje = hoje_de(a)
    escritorio = Path(a.escritorio) if a.escritorio else raiz.parent
    ents = carregar_indice(raiz)["entradas"]
    prob = []  # (quem resolve, id ou arquivo, problema e acao)

    caminhos = set()
    for e in ents:
        arq = raiz / e["caminho"]
        caminhos.add(arq.resolve())
        if not arq.is_file():
            prob.append(("script", e["id"], "arquivo sumiu; rode reindexar"))
            continue
        fim = valida_ate(e)
        if hoje > fim:
            prob.append(("diretor", e["id"], f"vencida em {fim}; renove so se tiver uso recente"))
        elif (fim - hoje).days <= a.aviso_dias:
            prob.append(("diretor", e["id"], f"vence em {fim}"))
        _, corpo = ler_frontmatter(arq.read_text(encoding="utf-8"))
        _, incerta = separar_resumo(e["resumo"])
        if "nao verificad" in norm(corpo) and not incerta:
            prob.append(("curador", e["id"], "corpo tem trechos nao verificados e o resumo nao tem 'Incertezas:'"))
        if len(e["resumo"]) < 200:
            prob.append(("curador", e["id"], f"resumo curto ({len(e['resumo'])} caracteres); diga a conclusao"))
        if len(e.get("tags", [])) < 5:
            prob.append(("curador", e["id"], f"so {len(e.get('tags', []))} tags; use 5 a 10, em portugues e ingles"))
        if e.get("nota") is None:
            prob.append(("curador", e["id"], "sem nota de curadoria"))

    for arq in sorted(raiz.glob("*/*.md")):
        if not arq.parent.name.startswith("_") and arq.resolve() not in caminhos:
            prob.append(("script", str(arq), "arquivo fora do indice; rode reindexar"))

    chaves = [(e["id"], set(tokens(e["titulo"] + " " + " ".join(e.get("tags", []))))) for e in ents]
    for i, (id1, t1) in enumerate(chaves):
        for id2, t2 in chaves[i + 1:]:
            jac = len(t1 & t2) / len(t1 | t2) if t1 | t2 else 0
            if jac >= a.sobreposicao:
                prob.append(("curador", f"{id1} + {id2}", f"assuntos parecidos (jaccard {jac:.2f}); avalie unir ou separar as tags"))

    for ped in sorted(escritorio.glob("*/pedidos/*.md")):
        meta, _ = ler_frontmatter(ped.read_text(encoding="utf-8"))
        if meta.get("status", "aberto").split()[0] != "respondido":
            dias = (hoje - date.fromtimestamp(ped.stat().st_mtime)).days
            prob.append(("diretor", str(ped.relative_to(escritorio.parent)), f"pedido aberto ha {dias} dia(s)"))

    log = raiz / "registro.jsonl"
    eventos = []
    if log.exists():
        for linha in log.read_text(encoding="utf-8").splitlines():
            try:
                eventos.append(json.loads(linha))
            except ValueError:
                continue
    # so o que veio depois da ultima revisao do curador (auditar --revisado)
    ultima = max((i for i, ev in enumerate(eventos) if ev.get("evento") == "REVISADO"), default=-1)
    eventos = eventos[ultima + 1:]
    for i, ev in enumerate(eventos):
        if ev.get("evento") != "HIT":
            continue
        q = set(tokens(ev.get("consulta", "")))
        for depois in eventos[i + 1:]:
            if depois.get("evento") == "ARQUIVADO":
                alvo = set(tokens(depois.get("id", "").replace("/", " ")))
                if q and len(q & alvo) / len(q) >= 0.4 and not depois.get("substituiu"):
                    alvo_hit = ev.get("alvo") or "pesquisa que deu HIT (nao registrada)"
                    prob.append(("curador", alvo_hit,
                                 f"possivel HIT falso: '{ev['consulta']}' deu HIT aqui e depois virou {depois['id']}; "
                                 "marque no resumo o que nao estava coberto ('Incertezas:') ou ajuste as tags"))
                break
    rotas = Counter(ev.get("evento") for ev in eventos if str(ev.get("evento", "")).startswith("ROTA_"))
    total = sum(rotas.values())
    if total >= 5 and rotas["ROTA_REGRA"] / total < 0.7:
        prob.append(("script", "roteamento.json",
                     f"so {rotas['ROTA_REGRA'] / total:.0%} das rotas por regra; acrescente palavras-chave"))

    print(f"AUDITORIA: {len(ents)} pesquisas, {len(prob)} problema(s)")
    for quem in ("curador", "diretor", "script"):
        itens = [p for p in prob if p[0] == quem]
        if itens:
            print(f"[{quem}]")
            for _, alvo, msg in itens:
                print(f"  - {alvo}: {msg}")
    if a.revisado:
        registrar(raiz, "REVISADO")
        print("REVISADO: avisos do registro anteriores a agora nao voltam a aparecer")
    precisa = any(p[0] == "curador" for p in prob)
    print("CURADOR: " + ("acione o agente curador-acervo so com os itens [curador]" if precisa
                         else "nao precisa (nada que exija julgamento)"))


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

    s = sp.add_parser("pedir", parents=[comum])
    s.add_argument("--de", required=True, help="andar que pede")
    s.add_argument("--para", default="pesquisa")
    s.add_argument("--pergunta", required=True)
    s.add_argument("--para-que", help="decisao que depende da resposta")
    s.add_argument("--criterio", action="append", default=[], help="criterio de respondida (repita)")
    s.add_argument("--palavras", help="3 a 6 palavras-chave para a busca no acervo")
    s.add_argument("--titulo", help="nome curto para o arquivo")
    s.add_argument("--nivel", default="padrao", help="rapida | padrao | profunda")
    s.add_argument("--escritorio", help="pasta dos andares (padrao: pasta acima do acervo)")
    s.add_argument("--forcar", action="store_true", help="grava mesmo com resposta parecida")
    s.set_defaults(f=cmd_pedir)

    s = sp.add_parser("triar", parents=[comum])
    s.add_argument("pedido")
    s.add_argument("--consulta", help="palavras para a busca (padrao: campo palavras do pedido)")
    s.add_argument("--tabela", default=str(TABELA_PADRAO))
    s.add_argument("--minimo", type=int, default=2)
    s.add_argument("--margem", type=int, default=1)
    s.add_argument("--rapida-ok", action="store_true", help="aceita nivel rapida num MISS")
    s.add_argument("--sem-resposta", action="store_true", help="no HIT, nao grava a resposta sozinho")
    s.add_argument("--escritorio")
    s.set_defaults(f=cmd_triar)

    s = sp.add_parser("responder", parents=[comum])
    s.add_argument("pedido")
    s.add_argument("--id", help="pesquisa do acervo que responde o pedido")
    s.add_argument("--descartar", help="motivo, quando a pesquisa foi descartada")
    s.add_argument("--escritorio")
    s.set_defaults(f=cmd_responder)

    s = sp.add_parser("checar", parents=[comum])
    s.add_argument("relatorio")
    s.add_argument("--nivel", default="padrao", help="rapida | padrao | profunda")
    s.set_defaults(f=cmd_checar)

    s = sp.add_parser("auditar", parents=[comum])
    s.add_argument("--escritorio", help="pasta dos andares (padrao: pasta acima do acervo)")
    s.add_argument("--aviso-dias", type=int, default=7, help="avisar o que vence nestes dias")
    s.add_argument("--sobreposicao", type=float, default=0.5, help="jaccard de titulo+tags para apontar duplicata")
    s.add_argument("--revisado", action="store_true", help="curador terminou: zera os avisos tirados do registro")
    s.set_defaults(f=cmd_auditar)

    s = sp.add_parser("stats", parents=[comum])
    s.add_argument("--custo-pesquisa", type=int, default=120000, help="tokens medios de uma pesquisa nova")
    s.add_argument("--custo-hit", type=int, default=6000, help="tokens medios para reaproveitar")
    s.set_defaults(f=cmd_stats)

    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
