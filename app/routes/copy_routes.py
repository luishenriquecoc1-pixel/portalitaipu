import random
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models import User, Content, CalendarEvent
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ==========================================
# TEMPLATES DE CONTEUDO
# ==========================================

CTAS = {
    "venda": [
        "Assine agora e navegue sem limites!",
        "Garanta ja o melhor plano para voce!",
        "Contrate hoje e ganhe instalacao gratis!",
        "Fale com um consultor e mude de internet agora!",
        "Aproveite: promocao por tempo limitado!",
        "Clique e conheca nossos planos!",
        "Ligue agora e comece a navegar em alta velocidade!",
        "Nao perca essa oferta — assine pelo site!",
        "Preencha o formulario e receba uma proposta personalizada!",
        "Migre para a Itaipu e sinta a diferenca desde o primeiro dia!",
    ],
    "branding": [
        "Conheca a internet que transforma sua experiencia!",
        "Descubra por que somos a escolha da regiao!",
        "Veja o que nossos clientes dizem!",
        "Faca parte da nossa comunidade conectada!",
        "Siga-nos para mais novidades e dicas!",
        "Conectar pessoas e o que nos move!",
        "Itaipu: tecnologia e confianca perto de voce!",
        "Acompanhe nossas redes e fique por dentro de tudo!",
    ],
    "engajamento": [
        "Conta pra gente nos comentarios: qual sua velocidade ideal?",
        "Marca aquele amigo que vive reclamando da internet!",
        "Salva esse post pra consultar depois!",
        "Compartilha com quem precisa de internet boa!",
        "Comenta aqui: voce usa internet mais pra trabalho ou lazer?",
        "Deixa um 🔥 se voce quer internet sem travamento!",
        "Qual desses beneficios e mais importante pra voce? Vota na enquete!",
        "Manda esse post pro grupo da familia!",
    ],
}

TONES = {
    "engraçado": {
        "opening": [
            "Sua internet ta mais lenta que fila de banco na segunda-feira? 😅",
            "Se sua internet fosse um animal, seria uma tartaruga aposentada? 🐢",
            "Ta esperando o video carregar desde 2019? ⏳",
            "Voce ja tentou conversar com seu roteador? Porque a gente tem uma solucao melhor!",
            "Sua internet cai mais que bebe aprendendo a andar? 😂",
            "Buffering... buffering... buffering... Cansou ne? A gente tambem!",
        ],
        "transition": [
            "Relaxa, a gente resolve isso! 😎",
            "Mas calma, tem solucao (e ela e rapida)!",
            "Chega de sofrimento digital!",
            "A era do travamento acabou!",
        ],
    },
    "direto": {
        "opening": [
            "Internet rapida, estavel e com preco justo.",
            "Chega de quedas. Chega de lentidao.",
            "Voce merece uma internet que funciona de verdade.",
            "Planos de internet com a melhor velocidade da regiao.",
            "Internet de qualidade nao precisa ser cara.",
            "Velocidade real. Sem surpresas na conta.",
        ],
        "transition": [
            "Nossos planos oferecem exatamente isso.",
            "E exatamente isso que entregamos.",
            "Simples assim. Sem letras miudas.",
            "Resultados que voce sente no dia a dia.",
        ],
    },
    "emocional": {
        "opening": [
            "Imagina assistir aquele filme em familia sem travamentos...",
            "Sabe aquele momento de trabalhar de casa com tranquilidade?",
            "A internet conecta voce ao que mais importa.",
            "Cada conexao e uma oportunidade de estar mais perto de quem voce ama.",
            "Aquela videochamada com quem ta longe... sem travar, sem cair.",
            "A melhor parte do dia e estar conectado com quem importa.",
        ],
        "transition": [
            "Com a nossa internet, isso e realidade.",
            "Nos tornamos isso possivel para voce e sua familia.",
            "E esse sentimento que queremos entregar todos os dias.",
            "Porque conexao de verdade vai alem da tecnologia.",
        ],
    },
    "profissional": {
        "opening": [
            "Sua empresa precisa de uma conexao que acompanhe o ritmo dos seus negocios.",
            "Produtividade comeca com infraestrutura de qualidade.",
            "No mundo corporativo, cada segundo de downtime custa caro.",
            "A conectividade da sua empresa define a eficiencia da sua operacao.",
            "Soluces de internet pensadas para quem leva negocios a serio.",
            "Sua operacao nao pode parar. Sua internet tambem nao.",
        ],
        "transition": [
            "Nossos planos empresariais foram desenhados para essa demanda.",
            "Oferecemos solucoes sob medida para o seu segmento.",
            "Tecnologia e suporte que sua empresa merece.",
            "Conte com uma infraestrutura robusta e confiavel.",
        ],
    },
    "urgente": {
        "opening": [
            "ULTIMAS VAGAS com desconto especial! Corre que ta acabando! 🔥",
            "ATENCAO: essa promocao termina HOJE!",
            "So restam poucas unidades com esse preco. Nao perca!",
            "OFERTA RELAMPAGO: internet com ate 50% de desconto!",
            "Voce vai perder essa oportunidade? O tempo ta correndo! ⏰",
            "ULTIMA CHANCE de garantir o melhor preco do ano!",
        ],
        "transition": [
            "Nao deixe pra depois — amanha o preco volta ao normal!",
            "Garanta agora antes que as vagas acabem!",
            "Quem fecha hoje, navega amanha com desconto!",
            "A oferta e por tempo LIMITADO!",
        ],
    },
}

PRODUCTS = {
    "planos de internet": {
        "features": [
            "Velocidade de ate 1 Gbps",
            "Wi-Fi de ultima geracao incluso",
            "Suporte tecnico 24 horas",
            "Instalacao rapida em ate 48h",
            "Sem fidelidade contratual",
            "Roteador dual band incluso",
        ],
        "benefits": [
            "Navegue, trabalhe e assista sem interrupcoes",
            "Conecte todos os dispositivos da casa ao mesmo tempo",
            "Estabilidade garantida para games e streaming",
            "Liberdade para usar como quiser, sem surpresas",
        ],
    },
    "fibra optica": {
        "features": [
            "Fibra 100% optica ate o seu endereco",
            "Menor latencia da regiao",
            "Upload simetrico de alta performance",
            "Roteador dual band de ultima geracao",
            "Sem oscilacao em horarios de pico",
            "Tecnologia GPON de ponta",
        ],
        "benefits": [
            "A tecnologia mais avancada chegando direto na sua casa",
            "Ideal para home office e streaming em 4K",
            "Conexao estavel mesmo nos horarios de maior demanda",
            "Performance real, nao apenas velocidade nominal",
        ],
    },
    "plano empresarial": {
        "features": [
            "IP fixo dedicado",
            "SLA com garantia de disponibilidade",
            "Link dedicado sob demanda",
            "Suporte prioritario com gerente de conta",
            "Monitoramento proativo 24/7",
            "Relatorios mensais de desempenho",
        ],
        "benefits": [
            "Sua empresa sempre conectada e produtiva",
            "Zero downtime para seus negocios criticos",
            "Velocidade e estabilidade que acompanham seu crescimento",
            "Tranquilidade para focar no que realmente importa",
        ],
    },
    "combo tv+internet": {
        "features": [
            "Mais de 150 canais em HD e Full HD",
            "Internet de alta velocidade inclusa",
            "Aplicativo para assistir no celular e tablet",
            "Gravador digital (DVR) incluso",
            "Canais premium com desconto exclusivo",
            "Wi-Fi mesh para cobertura total da casa",
        ],
        "benefits": [
            "Entretenimento completo para toda a familia num so pacote",
            "Assista seus programas favoritos sem travamento",
            "Economize combinando TV e internet em um unico plano",
            "A melhor experiencia de streaming e TV ao vivo juntas",
        ],
    },
    "plano gamer": {
        "features": [
            "Latencia ultra baixa (ping < 10ms)",
            "Velocidade simetrica de upload e download",
            "Prioridade de trafego para jogos online",
            "Roteador gamer com QoS integrado",
            "Porta dedicada para console ou PC",
            "Suporte especializado para gamers",
        ],
        "benefits": [
            "Jogue competitivamente sem lag e sem quedas",
            "Faca lives e streams em alta qualidade sem engasgar",
            "Atualizacoes e downloads de jogos em minutos, nao horas",
            "A conexao que nao te deixa na mao no ranked",
        ],
    },
    "internet rural": {
        "features": [
            "Cobertura em areas rurais e afastadas",
            "Tecnologia via radio e fibra hibrida",
            "Instalacao especializada no campo",
            "Equipamento resistente a intemperies",
            "Planos a partir de 50 Mbps",
            "Suporte tecnico presencial na regiao",
        ],
        "benefits": [
            "Leve internet de qualidade para o campo e o sitio",
            "Conecte sua propriedade rural ao mundo digital",
            "Ideal para agronegocio, monitoramento e gestao remota",
            "Nao fique isolado — tenha acesso a informacao e comunicacao",
        ],
    },
    "plano familia": {
        "features": [
            "Velocidade generosa para muitos dispositivos",
            "Controle parental integrado",
            "Wi-Fi mesh para cobertura em todos os comodos",
            "Ate 15 dispositivos simultaneos sem perda",
            "Perfis individuais para cada membro da familia",
            "Protecao contra sites maliciosos inclusa",
        ],
        "benefits": [
            "Toda a familia conectada ao mesmo tempo, sem brigas por internet",
            "Seguranca digital para as criancas navegarem tranquilas",
            "Streaming, aulas online e home office rodando juntos sem travar",
            "Internet que acompanha a rotina de uma familia moderna",
        ],
    },
    "plano start": {
        "features": [
            "Velocidade a partir de 100 Mbps",
            "Preco acessivel para todos os bolsos",
            "Sem taxa de instalacao",
            "Roteador Wi-Fi incluso",
            "Sem multa de cancelamento",
            "Ativacao em ate 24 horas",
        ],
        "benefits": [
            "A porta de entrada para internet de qualidade",
            "Perfeito pra quem quer gastar pouco e navegar bem",
            "Ideal para quem mora sozinho ou usa internet no basico",
            "Comece com um plano leve e faca upgrade quando quiser",
        ],
    },
}


# ==========================================
# FUNCOES GERADORAS DE CONTEUDO
# ==========================================

def generate_video_script_template(objective, audience, product_key, tone_key):
    tone = TONES.get(tone_key, TONES["direto"])
    product = PRODUCTS.get(product_key, list(PRODUCTS.values())[0])
    ctas = CTAS.get(objective, CTAS["venda"])

    opening = random.choice(tone["opening"])
    transition = random.choice(tone["transition"])
    features = random.sample(product["features"], min(3, len(product["features"])))
    benefits = random.sample(product["benefits"], min(2, len(product["benefits"])))
    cta = random.choice(ctas)

    return f"""ROTEIRO DE VIDEO - {product_key.upper()}
Publico-alvo: {audience}
Tom: {tone_key} | Objetivo: {objective}
Duracao estimada: 30-45 segundos
---

[CENA 1 - ABERTURA / GANCHO] (0-5s)
Texto/Fala: "{opening}"
Direcao visual: Close no rosto do apresentador ou animacao com texto grande. Musica de fundo energica.

[CENA 2 - TRANSICAO / EMPATIA] (5-10s)
Texto/Fala: "{transition}"
Direcao visual: Transicao rapida. Corte para imagens do produto/servico. Graficos em movimento.

[CENA 3 - APRESENTACAO DO PRODUTO] (10-18s)
Texto/Fala: "Com {product_key} da Itaipu, voce tem:"
- {features[0]}
- {features[1]}
- {features[2]}
Direcao visual: Cada feature aparece com icone animado. Fundo com cores da marca.

[CENA 4 - BENEFICIOS REAIS] (18-25s)
Texto/Fala: "{benefits[0]}"
Direcao visual: Mostrar situacao real de uso — pessoa usando internet feliz, familia assistindo TV, profissional trabalhando.

[CENA 5 - PROVA SOCIAL / REFORCO] (25-32s)
Texto/Fala: "{benefits[1]}"
Direcao visual: Depoimento rapido de cliente ou dados em graficos (ex: 99.5% de uptime, +10 mil clientes).

[CENA 6 - CTA FINAL] (32-40s)
Texto/Fala: "{cta}"
Direcao visual: Tela com logo Itaipu, telefone, site e QR code. Musica fecha com impacto.

---
Observacoes de producao:
- Formato: vertical (9:16) para Reels/Stories ou horizontal (16:9) para YouTube
- Legendas obrigatorias em todas as cenas
- Inserir logo Itaipu no canto superior durante todo o video"""


def generate_post_copy_template(objective, audience, product_key, tone_key):
    tone = TONES.get(tone_key, TONES["direto"])
    product = PRODUCTS.get(product_key, list(PRODUCTS.values())[0])
    ctas = CTAS.get(objective, CTAS["venda"])

    opening = random.choice(tone["opening"])
    feature1 = random.choice(product["features"])
    feature2 = random.choice([f for f in product["features"] if f != feature1])
    benefit = random.choice(product["benefits"])
    cta = random.choice(ctas)

    emoji_sets = [
        {"header": "🚀", "check": "✅", "point": "👉", "fire": "🔥"},
        {"header": "⚡", "check": "✔️", "point": "➡️", "fire": "💥"},
        {"header": "💡", "check": "☑️", "point": "📌", "fire": "🌟"},
    ]
    emojis = random.choice(emoji_sets)

    hashtags_pool = [
        "#internet", "#fibraoptica", "#conexao", "#wifirapido",
        "#provedor", "#itaipu", "#internetrapida", "#tecnologia",
        "#conectividade", "#streaming", "#homeoffice", "#semtravamento",
        "#internetfibra", "#velocidade", "#naveguesemparar",
    ]
    selected_hashtags = " ".join(random.sample(hashtags_pool, 6))

    return f"""{emojis["header"]} {opening}

{benefit} com {product_key} da Itaipu! {emojis["fire"]}

{emojis["check"]} {feature1}
{emojis["check"]} {feature2}

{emojis["point"]} {cta}

---
{selected_hashtags}"""


def generate_ad_text_template(objective, audience, product_key, tone_key):
    tone = TONES.get(tone_key, TONES["direto"])
    product = PRODUCTS.get(product_key, list(PRODUCTS.values())[0])
    ctas = CTAS.get(objective, CTAS["venda"])

    headline = random.choice(product["benefits"])
    feature1 = random.choice(product["features"])
    feature2 = random.choice([f for f in product["features"] if f != feature1])
    cta = random.choice(ctas)
    opening = random.choice(tone["opening"])

    return f"""===== VARIACAO 1 - CURTA (Feed / Display) =====
TITULO: {headline}
DESCRICAO: {feature1}. Planos de {product_key} para {audience}.
CTA: {cta}

===== VARIACAO 2 - URGENCIA (Stories / Promocional) =====
TITULO: OFERTA POR TEMPO LIMITADO!
DESCRICAO: {opening} Aproveite {product_key} com {feature1.lower()} e {feature2.lower()}. So ate amanha!
CTA: Garanta ja o seu plano!

===== VARIACAO 3 - PROVA SOCIAL (Feed / Carrossel) =====
TITULO: Mais de 10.000 clientes ja escolheram Itaipu
DESCRICAO: {headline}. {feature1}. Faca como milhares de pessoas na regiao.
CTA: {cta}

===== VARIACAO 4 - BENEFICIO DIRETO (Google Ads / Search) =====
TITULO: {feature1} | {product_key.title()} Itaipu
DESCRICAO: {headline}. {feature2}. A melhor opcao para {audience}.
CTA: Conheca nossos planos e contrate online!"""


def generate_story_copy_template(objective, audience, product_key, tone_key):
    tone = TONES.get(tone_key, TONES["direto"])
    product = PRODUCTS.get(product_key, list(PRODUCTS.values())[0])
    ctas = CTAS.get(objective, CTAS["venda"])

    opening = random.choice(tone["opening"])
    feature = random.choice(product["features"])
    cta = random.choice(ctas)

    emoji_options = ["🚀", "⚡", "🔥", "💥", "📶", "💡", "✨"]
    emoji = random.choice(emoji_options)

    templates_list = [
        f"""{emoji} {opening}

{feature}

👉 {cta}""",
        f"""{opening} {emoji}

✅ {feature}

{cta} ⬆️ Link na bio!""",
        f"""{emoji} {random.choice(product["benefits"])}

{feature}

Arrasta pra cima! 👆 {cta}""",
        f"""{opening}

{emoji} {feature}

💬 {cta}""",
    ]

    return random.choice(templates_list)


def generate_with_templates(objective, audience, product, tone):
    return {
        "video_script": generate_video_script_template(objective, audience, product, tone),
        "post_copy": generate_post_copy_template(objective, audience, product, tone),
        "ad_text": generate_ad_text_template(objective, audience, product, tone),
        "story_copy": generate_story_copy_template(objective, audience, product, tone),
        "cta": random.choice(CTAS.get(objective, CTAS["venda"])),
    }


# ==========================================
# ROUTES
# ==========================================

@router.get("/copy", response_class=HTMLResponse)
async def copy_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("copy.html", {
        "request": request,
        "user": user,
        "page": "copy",
        "products": list(PRODUCTS.keys()),
        "tones": list(TONES.keys()),
    })


@router.post("/api/copy/generate", tags=["copy"])
async def generate_copy(request: Request, user: User = Depends(get_current_user)):
    data = await request.json()
    objective = data.get("objective", "venda")
    audience = data.get("audience", "publico geral")
    product = data.get("product", "planos de internet")
    tone = data.get("tone", "direto")

    return generate_with_templates(objective, audience, product, tone)


@router.post("/api/copy/to-production", tags=["copy"])
async def copy_to_production(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await request.json()

    title = data.get("title", "Conteudo sem titulo")
    description = data.get("description", "")
    content_type = data.get("content_type", "post")
    due_date_str = data.get("due_date")
    priority = data.get("priority", "media")
    copy_text = data.get("copy_text", "")

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Formato de data invalido. Use AAAA-MM-DD."}, 400

    content = Content(
        title=title,
        description=f"{description}\n\n---\nCopy gerada:\n{copy_text}" if copy_text else description,
        content_type=content_type,
        status="producao",
        responsible_id=user.id,
        due_date=due_date,
        priority=priority,
    )
    db.add(content)
    db.flush()

    event = None
    event_id = None
    if due_date:
        event = CalendarEvent(
            title=f"[Post] {title}",
            event_type="post",
            date=due_date,
            description=description,
            content_id=content.id,
            all_day=True,
        )
        db.add(event)
        db.flush()
        event_id = event.id

    db.commit()

    return {
        "content_id": content.id,
        "event_id": event_id,
    }
