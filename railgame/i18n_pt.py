"""Portuguese texts (European Portuguese), used by i18n.t() when Portuguese is chosen.

PT: whole texts. PT_PATTERNS: texts with names or numbers in them, as (regular expression,
Portuguese with {} for each group); each group is translated too when it can be.
"""

from railgame import i18n

PT: dict[str, str] = {
    # ---------------------------------------------------------------- menus
    "Language": "Idioma",
    "You control the signals and points of a Portuguese railway line. Keep the trains moving, "
    "keep them apart, keep them on time.":
        "Controlas os sinais e as agulhas de uma linha ferroviária portuguesa. Mantém os comboios "
        "em andamento, afastados uns dos outros e a horas.",
    "Choose a line": "Escolhe uma linha",
    "How it works": "Como funciona",
    "The line has a single track. Trains in opposite directions can only pass each other at "
    "crossing stations (two tracks).":
        "A linha tem uma só via. Comboios em sentidos opostos só se cruzam nas estações de "
        "cruzamento (com duas vias).",
    "Drivers send you requests. Each one stays on screen until you do what it asks.":
        "Os maquinistas enviam-te pedidos. Cada um fica no ecrã até fazeres o que pede.",
    "Click a signal to turn it green or red. It turns red again after a train passes.":
        "Clica num sinal para o pôr verde ou vermelho. Volta a vermelho depois de um comboio passar.",
    "Click a set of points to send trains to track 1 (straight) or track 2 (yellow).":
        "Clica numa agulha para mandar os comboios para a via 1 (em frente) ou para a via 2 (amarelo).",
    "Two trains on the same track = accident. Too much average delay = repeat the level.":
        "Dois comboios na mesma via = acidente. Atraso médio a mais = repetir o nível.",
    "Customise": "Personalizar",
    "Quit": "Sair",
    "Back": "Voltar",
    "Levels": "Níveis",
    "Replay": "Jogar de novo",
    "Next level": "Nível seguinte",
    "Try again": "Tentar de novo",
    "Loading…": "A carregar…",
    "Line blocked": "Linha bloqueada",
    "Click to choose. Your choice is saved for next time.":
        "Clica para escolher. A escolha fica guardada para a próxima vez.",
    "Map colours": "Cores do mapa",
    # ---------------------------------------------------------------- my levels (the editor)
    "My levels": "Os meus níveis",
    "My level": "O meu nível",
    "Level editor": "Editor de níveis",
    "Make your own line, choose the trains and their times, then play it.":
        "Faz a tua própria linha, escolhe os comboios e os horários, e depois joga.",
    "No levels yet. Make the first one!": "Ainda não há níveis. Faz o primeiro!",
    "Play": "Jogar",
    "Edit": "Editar",
    "Delete": "Apagar",
    "Sure?": "De certeza?",
    "New level": "Novo nível",
    "The line": "A linha",
    "Shape": "Forma",
    "Landscape": "Paisagem",
    "Station": "Estação",
    "Type": "Tipo",
    "Distance to the next": "Distância até à seguinte",
    "Crossing": "Cruzamento",
    "Halt": "Apeadeiro",
    "+ Station": "+ Estação",
    "The trains": "Os comboios",
    "Allowed average delay": "Atraso médio permitido",
    "Train": "Comboio",
    "From": "De",
    "Enters the map at": "Entra no mapa às",
    "+ Train": "+ Comboio",
    "Sort by time": "Ordenar por hora",
    "Save": "Guardar",
    "Save and play": "Guardar e jogar",
    "Saved.": "Guardado.",
    "Could not write the file: the level is kept until you close the game.":
        "Não foi possível escrever o ficheiro: o nível fica guardado até fechares o jogo.",
    "Click a name to type. The level starts two minutes before the first train.":
        "Clica num nome para escrever. O nível começa dois minutos antes do primeiro comboio.",
    "A line needs at least two stations.": "Uma linha precisa de pelo menos duas estações.",
    "At least two stations must be crossing stations.":
        "Pelo menos duas estações têm de ser de cruzamento.",
    "Every station needs a name.": "Todas as estações precisam de um nome.",
    "Two stations have the same name.": "Há duas estações com o mesmo nome.",
    "Add at least one train.": "Acrescenta pelo menos um comboio.",
    "Gentle curve": "Curva suave",
    "Straight": "Reta",
    "Big bend": "Curva grande",
    "S-curve": "Curva em S",
    "South to north": "De sul para norte",
    "Coast": "Costa",
    "Plain": "Planície",
    "River valley": "Vale de um rio",
    "Simple map": "Mapa simples",
    "River": "Rio",
    "Drawn by hand": "Desenhada à mão",
    "Draw by hand": "Desenhar à mão",
    "Draw the line": "Desenha a linha",
    "Hold the mouse button down and draw the line across the map, from the first station to the last.":
        "Carrega no botão do rato e desenha a linha pelo mapa, da primeira estação até à última.",
    "Draw here": "Desenha aqui",
    "This is your line, with its stations. Draw again to change it.":
        "Esta é a tua linha, com as estações. Desenha outra vez para a mudar.",
    "Use this line": "Usar esta linha",
    "Branch line": "Ramal",
    "A second line that leaves the first one just past one of its crossing stations.":
        "Uma segunda linha que sai da primeira logo a seguir a uma das suas estações de cruzamento.",
    "Trains can run from the first station of the line to the end of the branch, and back. "
    "At the junction you set the points for each train: the driver tells you which way he is going.":
        "Os comboios podem ir da primeira estação da linha até ao fim do ramal, e voltar. "
        "Na bifurcação és tu que pões a agulha para cada comboio: o maquinista diz-te para onde vai.",
    "Add a branch": "Adicionar um ramal",
    "Remove the branch": "Remover o ramal",
    "Done": "Feito",
    "Leaves from": "Sai de",
    "Distance from there to the first station of the branch": "Distância daí até à primeira estação do ramal",
    "In the list of trains, click a train's route to send it along the branch. "
    "The branch ends at its last station and goes on off the map.":
        "Na lista de comboios, clica no percurso de um comboio para o mandares pelo ramal. "
        "O ramal acaba na sua última estação e continua para fora do mapa.",
    "Route": "Percurso",
    "with a branch": "com ramal",
    "The branch needs at least one station.": "O ramal precisa de pelo menos uma estação.",
    "The branch must leave from a crossing station.": "O ramal tem de sair de uma estação de cruzamento.",
    # The second line and double track (level editor).
    "Second line": "Segunda linha",
    "Double track": "Via dupla",
    "Kind": "Tipo",
    "Branch": "Ramal",
    "Crossing line": "Linha que cruza",
    "Separate line": "Linha separada",
    "+ Branch": "+ Ramal",
    "+ Crossing line": "+ Linha que cruza",
    "+ Separate line": "+ Linha separada",
    "A line that leaves the first one just past one of its crossing stations.":
        "Uma linha que sai da primeira logo a seguir a uma das suas estações de cruzamento.",
    "A line that comes in from one side, runs through a crossing station of the first one and leaves on the other side.":
        "Uma linha que entra por um lado, passa por uma estação de cruzamento da primeira e sai pelo outro lado.",
    "A line of its own on the same map, which never meets the first one.":
        "Uma linha só dela no mesmo mapa, que nunca se encontra com a primeira.",
    "Add a second line to the level. Trains can then run on either line.":
        "Junta uma segunda linha ao nível. Os comboios podem andar em qualquer uma das linhas.",
    "Where two lines meet you set the points for each train: the driver tells you which way he is going. "
    "For two tracks on the whole main line, use Double track in the editor.":
        "Onde as linhas se encontram és tu que pões a agulha para cada comboio: o maquinista diz-te para onde vai. "
        "Para ter duas vias na linha principal toda, usa Via dupla no editor.",
    "Crosses at": "Cruza em",
    "Before it": "Antes dela",
    "Shared": "Partilhada",
    "In the list of trains, click a train's route to send it along the second line. "
    "The second line goes on off the map at its ends.":
        "Na lista de comboios, clica no percurso de um comboio para o mandares pela segunda linha. "
        "A segunda linha continua para fora do mapa nas pontas.",
    "Remove the second line": "Remover a segunda linha",
    "The map shows once the level has no problems.": "O mapa aparece quando o nível não tiver problemas.",
    "The second line needs at least one station.": "A segunda linha precisa de pelo menos uma estação.",
    "The second line must meet the first at a crossing station.":
        "A segunda linha tem de se encontrar com a primeira numa estação de cruzamento.",
    "With double track the second line can only be a separate line.":
        "Com via dupla a segunda linha só pode ser uma linha separada.",
    "double track": "via dupla",
    "with a second line": "com segunda linha",
    "Clear": "Limpar",
    "Cancel": "Cancelar",
    "Hold the mouse button down and draw the line.": "Carrega no botão do rato e desenha a linha.",
    "The line is too short. Draw it across the map.": "A linha é curta demais. Desenha-a pelo mapa fora.",
    "The line cannot cross itself.": "A linha não se pode cruzar com ela própria.",
    "That bend is too sharp for a train. Draw wider curves.":
        "Essa curva é apertada demais para um comboio. Desenha curvas mais largas.",
    "Fast trains: keep them off the slow tracks": "Comboios rápidos: mantém-nos fora das vias lentas",
    # Where each line goes, and its trains.
    "Faro to Tavira, along the Ria Formosa.": "De Faro a Tavira, ao longo da Ria Formosa.",
    "Torres Vedras to Caldas da Rainha, north along the coast.":
        "De Torres Vedras às Caldas da Rainha, para norte ao longo da costa.",
    "Peso da Régua to Ferradosa, along the river.": "Do Peso da Régua à Ferradosa, ao longo do rio.",
    "Casa Branca to Beja, across the plain.": "De Casa Branca a Beja, através da planície.",
    "Santa Apolónia to Oriente, four tracks by the Tejo.":
        "De Santa Apolónia ao Oriente, quatro vias junto ao Tejo.",
    "Regional": "Regional",
    "Inter-Regional": "Inter-Regional",
    "Freight": "Mercadorias",
    "Historic": "Histórico",
    "Historic steam": "Histórico a vapor",
    # Themes and train skins.
    "Night": "Noite",
    "Day": "Dia",
    "Sunset": "Pôr do sol",
    "Control room": "Sala de controlo",
    "Real": "Real",
    "Vintage": "Clássico",
    "Modern": "Moderno",
    "Futuristic": "Futurista",
    "Jade dragon": "Dragão de jade",
    "Diamond": "Diamante",
    "Steam": "Vapor",
    "Fire dragon": "Dragão de fogo",
    "Ruby": "Rubi",
    "Ice dragon": "Dragão de gelo",
    "Emerald": "Esmeralda",
    "Royal": "Comboio real",
    "Panoramic": "Panorâmico",
    "Iron dragon": "Dragão de ferro",
    "Amethyst": "Ametista",
    "Storm dragon": "Dragão da tempestade",
    "Sapphire": "Safira",
    "Sea serpent": "Serpente marinha",
    "Topaz": "Topázio",
    # ---------------------------------------------------------------- playing
    "Pause": "Pausa",
    "Restart": "Reiniciar",
    "Menu": "Menu",
    "Drivers' requests": "Pedidos dos maquinistas",
    "Do it": "Fazer",
    "All quiet on the line.": "Tudo calmo na linha.",
    "When a train comes, its driver asks you for something here: a green signal or the points "
    "set for a track. Click the signal or points that pulse on the map, or press Do it on the request.":
        "Quando chega um comboio, o maquinista pede-te aqui alguma coisa: um sinal verde ou a "
        "agulha posta para uma via. Clica no sinal ou na agulha que pulsa no mapa, ou carrega em "
        "Fazer no pedido.",
    "now": "agora",
    "Next trains": "Próximos comboios",
    "No more trains to come.": "Não vêm mais comboios.",
    "delayed": "atrasado",
    "on time": "a horas",
    "did not start": "não partiu",
    "How to play": "Como jogar",
    "Click a signal: red ↔ green": "Clica num sinal: vermelho ↔ verde",
    "Click points: white straight, yellow the other way": "Agulha: branco em frente, amarelo desvia",
    "Pulsing ring: a driver is waiting for it": "Anel a pulsar: um maquinista está à espera",
    "Space pause · 1/2/3/4 speed · R restart · Esc levels":
        "Espaço pausa · 1-4 veloc. · R reinicia · Esc níveis",
    "leaving the map": "a sair do mapa",
    "green": "verde",
    "red": "vermelho",
    "The level is over.": "O nível terminou.",
    "Accident!": "Acidente!",
    "Level complete": "Nível concluído",
    "Too much delay": "Atraso a mais",
    # Words on the maps (most are Portuguese names already).
    "Atlantic Ocean": "Oceano Atlântico",
    "W": "O",  # the compass: oeste
    # ---------------------------------------------------------------- levels
    "First shift": "Primeiro turno",
    "Two trains, one crossing. Learn how signals and points work.":
        "Dois comboios, um cruzamento. Aprende como funcionam os sinais e as agulhas.",
    "Second crossing": "Segundo cruzamento",
    "Three trains. The third one crosses somewhere else.": "Três comboios. O terceiro cruza noutro sítio.",
    "Morning service": "Serviço da manhã",
    "Four trains. Decide where each pair crosses.": "Quatro comboios. Decide onde se cruza cada par.",
    "The Inter-Regional": "O Inter-Regional",
    "An IR train skips the small halts and catches up with the regionals.":
        "Um comboio IR não para nos apeadeiros e apanha os regionais.",
    "Rush hour": "Hora de ponta",
    "Six trains in less than an hour. Keep the requests under control.":
        "Seis comboios em menos de uma hora. Mantém os pedidos sob controlo.",
    "Market day in Olhão": "Dia de mercado em Olhão",
    "Six trains with two IRs. Some pairs arrive at the same time.":
        "Seis comboios com dois IR. Alguns pares chegam ao mesmo tempo.",
    "Beach traffic": "Trânsito de praia",
    "Seven trains, often two at a time.": "Sete comboios, muitas vezes dois de cada vez.",
    "Summer chaos": "Caos de verão",
    "Eight trains, two at a time. Only the best controllers keep the delay down.":
        "Oito comboios, dois de cada vez. Só os melhores controladores mantêm o atraso baixo.",
    "Running late": "Atrasados",
    "Up the coast": "Pela costa acima",
    "Two regionals on the Linha do Oeste, a long line with four crossing stations.":
        "Dois regionais na Linha do Oeste, uma linha longa com quatro estações de cruzamento.",
    "The first freight": "O primeiro mercadorias",
    "A freight train (M) is slow and long, and never stops at a station unless a signal is red.":
        "Um comboio de mercadorias (M) é lento e comprido, e só para numa estação se o sinal estiver vermelho.",
    "Freight on the coast": "Mercadorias na costa",
    "The freight train has to let the regionals cross it. Find it a place to wait.":
        "O mercadorias tem de deixar passar os regionais. Arranja-lhe um sítio para esperar.",
    "Behind the freight": "Atrás do mercadorias",
    "A regional follows the freight train in the same direction.":
        "Um regional segue o comboio de mercadorias no mesmo sentido.",
    "Market day": "Dia de mercado",
    "Regionals both ways and a freight train in the middle of them.":
        "Regionais nos dois sentidos e um comboio de mercadorias no meio deles.",
    "Two freights": "Dois mercadorias",
    "Freight trains in both directions. They need the long gaps between regionals.":
        "Comboios de mercadorias nos dois sentidos. Precisam dos intervalos longos entre os regionais.",
    "Cement and passengers": "Cimento e passageiros",
    "Two freight trains against the passenger service. Decide who waits.":
        "Dois comboios de mercadorias contra o serviço de passageiros. Decide quem espera.",
    "Night of the freights": "A noite dos mercadorias",
    "Eight trains, three of them freight. Only the best controllers keep the line moving.":
        "Oito comboios, três deles de mercadorias. Só os melhores controladores mantêm a linha a andar.",
    "Along the river": "Ao longo do rio",
    "Two regionals on the Linha do Douro. The single-track sections are long.":
        "Dois regionais na Linha do Douro. Os troços de via única são longos.",
    "Wine country": "Terra do vinho",
    "Three trains. Plan where the second regional crosses.":
        "Três comboios. Planeia onde cruza o segundo regional.",
    "Steam!": "Vapor!",
    "The historic steam train (H) is slow and stays a long time at Pinhão.":
        "O comboio histórico a vapor (H) é lento e fica muito tempo no Pinhão.",
    "Overtaking the steam train": "Ultrapassar o comboio a vapor",
    "A regional catches up with the steam train. Let it pass at a station.":
        "Um regional apanha o comboio a vapor. Deixa-o passar numa estação.",
    "Steam on the Douro": "Vapor no Douro",
    "Steam, regionals and an IR. Plan around the slow train.":
        "Vapor, regionais e um IR. Planeia à volta do comboio lento.",
    "Two steam trains": "Dois comboios a vapor",
    "Steam trains in both directions meet somewhere on the line.":
        "Comboios a vapor nos dois sentidos encontram-se algures na linha.",
    "Harvest season": "Época das vindimas",
    "Steam trains both ways, regionals and IRs. Only for expert controllers.":
        "Comboios a vapor nos dois sentidos, regionais e IR. Só para controladores experientes.",
    "Santa Apolónia": "Santa Apolónia",
    "A terminus: trains to Lisbon end here, trains from Lisbon start here. One out, one in.":
        "Uma estação terminal: os comboios para Lisboa acabam aqui e os de Lisboa partem daqui. Um sai, outro entra.",
    "The Alfa Pendular": "O Alfa Pendular",
    "The Alfa is fast. After Braço de Prata send it onto the fast track, away from the regionals.":
        "O Alfa é rápido. Depois de Braço de Prata manda-o para a via rápida, longe dos regionais.",
    "Four platforms": "Quatro linhas",
    "Trains in and out at the same time. Keep arrivals and departures on their own platforms.":
        "Comboios a entrar e a sair ao mesmo tempo. Mantém chegadas e partidas nas suas próprias linhas.",
    "The Cintura line": "A Linha de Cintura",
    "Trains from Sintra join at Braço de Prata, and some trains from the north go off to Sintra.":
        "Os comboios de Sintra entram em Braço de Prata, e alguns comboios do norte seguem para Sintra.",
    "Overtaking at Oriente": "Ultrapassagem no Oriente",
    "The regional leaves first, the Intercidades soon after. Let the fast train pass at Oriente.":
        "O regional parte primeiro e o Intercidades logo a seguir. Deixa o comboio rápido passar no Oriente.",
    "Freight to Alcântara": "Rumo a Alcântara",
    "A long, slow freight train comes down from the north and turns off onto the Cintura line.":
        "Um mercadorias comprido e lento desce do norte e sai para a Linha de Cintura.",
    "Full house": "Casa cheia",
    "More trains arrive than platforms 3 and 4 can take. Use the crossover to platforms 1 and 2.":
        "Chegam mais comboios do que as linhas 3 e 4 aguentam. Usa a diagonal para as linhas 1 e 2.",
    "Morning rush": "Ponta da manhã",
    "The busiest hour of the day: Alfas, Intercidades, regionals, the Cintura and a freight.":
        "A hora mais movimentada do dia: Alfas, Intercidades, regionais, a Cintura e um mercadorias.",
    "Across the plain": "Através da planície",
    "Two regionals between Casa Branca and Beja. The line is long: plan where they cross.":
        "Dois regionais entre Casa Branca e Beja. A linha é longa: planeia onde se cruzam.",
    "The long section": "O troço longo",
    "Intercidades to Beja": "Intercidades para Beja",
    "The Intercidades (IC) from Lisbon is fast and only stops at the crossing stations.":
        "O Intercidades (IC) de Lisboa é rápido e só para nas estações de cruzamento.",
    "The grain train": "O comboio do cereal",
    "A long freight train (M) brings grain from Beja. It is slow: do not let it hold up the others.":
        "Um comboio de mercadorias (M) comprido traz cereal de Beja. É lento: não o deixes atrasar os outros.",
    "Market day in Beja": "Dia de mercado em Beja",
    "Five trains on a market morning, crossing at every station.":
        "Cinco comboios numa manhã de mercado, a cruzarem-se em todas as estações.",
    "Harvest": "Colheita",
    "Two grain trains and the regionals. Find the freights a quiet place to wait.":
        "Dois comboios de cereal e os regionais. Arranja aos mercadorias um sítio calmo para esperar.",
    "Summer heat": "Calor de verão",
    "Seven trains on a hot afternoon, two at a time.": "Sete comboios numa tarde quente, dois de cada vez.",
    "Feira de Beja": "Feira de Beja",
    "Eight trains for the Beja fair. Only the best controllers keep the plain moving.":
        "Oito comboios para a feira de Beja. Só os melhores controladores mantêm a planície a andar.",
}

# Lisbon's tracks, as the drivers name them (all feminine: via, linha).
TRACKS = {
    "the northbound track": "via sentido norte",
    "the southbound track": "via sentido sul",
    "the northbound fast track": "via rápida sentido norte",
    "the southbound fast track": "via rápida sentido sul",
    "the Cintura line": "Linha de Cintura",
    # A line with a branch, made in the level editor.
    "the main line": "linha principal",
    "the branch line": "linha do ramal",
    "the eastbound track": "via sentido nascente",
    "the westbound track": "via sentido poente",
    "the crossing line": "linha que cruza",
    "the second line": "segunda linha",
}


def track(name: str) -> str:
    if name.startswith("platform "):
        return "linha " + name.split()[1]
    if name.startswith("track "):
        return "via " + name.split()[1]
    return TRACKS.get(name, name)


# Places said with an article in Portuguese ("do Peso da Régua", "às Caldas da Rainha").
ARTICLES = {
    "Peso da Régua": "o", "Pinhão": "o", "Tua": "o", "Porto": "o", "Pocinho": "o", "Oriente": "o",
    "Bombarral": "o", "Ramalhal": "o", "Livramento": "o", "Outeiro": "o", "Ferrão": "o",
    "Ferradosa": "a", "Fuseta": "a", "Azambuja": "a", "Bobadela": "a", "Funcheira": "a",
    "Caldas da Rainha": "as",
}
_JOIN = {
    "de": {"o": "do", "a": "da", "as": "das"},
    "a": {"o": "ao", "a": "à", "as": "às"},
    "em": {"o": "no", "a": "na", "as": "nas"},
    "para": {"o": "para o", "a": "para a", "as": "para as"},
}


def to(word: str, place: str) -> str:
    """'de' + 'Peso da Régua' -> 'do Peso da Régua'; 'a' + 'Faro' -> 'a Faro'."""
    article = ARTICLES.get(place)
    return f"{_JOIN[word][article] if article else word} {place}"


def minutes(text: str) -> str:
    """'7.7 min' -> '7,7 min'"""
    return i18n.decimal(text)


PT_PATTERNS: list = [
    # Titles and labels made of parts: "Level 3 · Rush hour", "R · Regional", "Regional · Freight".
    (r"Level (\d+) · (.+)", lambda n, title: f"Nível {n} · {i18n.t(title, False)}"),
    (r"(.+)  ✓", lambda name: f"{i18n.t(name, False)}  ✓"),
    (r"Language: (.+)", "Idioma: {}"),
    (r"(\d+) levels", "{} níveis"),
    (r"(\d+) stations \((\d+) crossing\)", "{} estações ({} de cruzamento)"),
    (r"(\d+) stations, (\d+) km\. Made in the level editor\.", "{} estações, {} km. Feito no editor de níveis."),
    (r"(\d+) stations, (\d+) km(, double track)?( and a branch| and a crossing line| and a second line)?\. "
     r"Made in the level editor\.",
     lambda n, km, double, second: f"{n} estações, {km} km"
     + (", via dupla" if double else "")
     + {None: "", " and a branch": " e um ramal", " and a crossing line": " e uma linha que cruza",
        " and a second line": " e uma segunda linha"}[second]
     + ". Feito no editor de níveis."),
    (r"The list is full \((\d+) levels\)\. Delete one to make another\.",
     "A lista está cheia ({} níveis). Apaga um para fazeres outro."),
    (r"Trains: (.+)", lambda trains: f"Comboios: {i18n.t(trains, False)}"),
    (r"(.+?)  Trains: (.+)\.", lambda where, trains: f"{i18n.t(where, False)}  Comboios: {i18n.t(trains, False)}."),
    (r"(\d+) trains · limit (\d+) min", "{} comboios · limite {} min"),
    (r"Drawing the map of the (.+) for level (\d+)", "A desenhar o mapa da {} para o nível {}"),
    (r"Level (\d+)'s trains, but some reach the map late, and never the same ones twice\. "
     r"Their own lateness is not counted, only the delay you add\.",
     "Os comboios do nível {}, mas alguns chegam ao mapa atrasados, e nunca os mesmos duas vezes. "
     "O atraso que já trazem não conta, só o que tu acrescentas."),
    (r"Between (.+) and (.+) there are (\d+) km of single track and nowhere to cross\.",
     "Entre {} e {} há {} km de via única e nenhum sítio para cruzar."),
    # Top bar, panels and the result.
    (r"Average delay ([\d.]+ min)", lambda m: f"Atraso médio {minutes(m)}"),
    (r"\(limit (\d+) min\)", "(limite {} min)"),
    (r"Trains done (\d+)/(\d+)", "Comboios concluídos {}/{}"),
    (r"(\d+) min ago", "há {} min"),
    (r"\+ (\d+) more…", "+ {} mais…"),
    (r"from (.+)", lambda p: to("de", p)),
    (r"to (.+)", lambda p: to("para", p)),
    (r"delayed (\d+) min", "atrasado {} min"),
    (r"\+([\d.]+ min)", lambda m: "+" + minutes(m)),
    (r"Click points: white straight, yellow to track (\d+)", "Agulha: branco em frente, amarelo para a via {}"),
    (r"(.+) and (.+) collided\. Never let two trains onto the same track\.",
     "O {} e o {} colidiram. Nunca deixes dois comboios entrar na mesma via."),
    (r"(\d+) trains can never move again: each one is waiting for another\. "
     r"Keep a track free at every station for trains coming the other way\.",
     "{} comboios já não se podem mexer: cada um está à espera de outro. "
     "Deixa uma via livre em cada estação para os comboios que vêm em sentido contrário."),
    (r"(.+) can never move again: each one is waiting for another\. "
     r"Keep a track free at every station for trains coming the other way\.",
     "{} já não se podem mexer: cada um está à espera de outro. "
     "Deixa uma via livre em cada estação para os comboios que vêm em sentido contrário."),
    (r"Average delay ([\d.]+ min)\. Well done, controller\.",
     lambda m: f"Atraso médio {minutes(m)}. Muito bem, controlador."),
    (r"Average delay ([\d.]+ min), the limit is (\d+) min\. Try again\.",
     lambda m, limit: f"Atraso médio {minutes(m)}, o limite é {limit} min. Tenta de novo."),
    # What the drivers and the line say.
    (r"Running (\d+) min late\. We'll reach the map at (\d+:\d+)\.",
     "Vamos com {} min de atraso. Chegamos ao mapa às {}."),
    (r"Set the points at (.+) for track (\d+) first\.", lambda st, n: f"Primeiro põe a agulha {to('de', st)} para a via {n}."),
    (r"Points at (.+) are locked: (.+) is passing over them\.",
     lambda st, tr: f"A agulha {to('de', st)} está bloqueada: o {tr} está a passar por ela."),
    (r"Points at (.+) are locked: signal (.+) is green over them\.",
     lambda st, sg: f"A agulha {to('de', st)} está bloqueada: o sinal {sg} está verde por cima dela."),
    (r"Points at (.+) are locked: (.+) is on its way over them\.",
     lambda st, tr: f"A agulha {to('de', st)} está bloqueada: o {tr} vai passar por ela."),
    (r"Points (\S+) are locked: (.+) is passing over them\.",
     "A agulha {} está bloqueada: o {} está a passar por ela."),
    (r"Points (\S+) are locked: (.+) is about to go over them\.",
     "A agulha {} está bloqueada: o {} está prestes a passar por ela."),
    (r"Approaching (.+)\. Please set the points to track (\d+) for me\.",
     lambda st, n: f"A chegar {to('a', st)}. Põe a agulha para a via {n}, por favor."),
    (r"I'm on track (\d+) at (.+)\. Please set the points so I can get out\.",
     lambda n, st: f"Estou na via {n} {to('em', st)}. Põe a agulha para eu poder sair, por favor."),
    (r"Approaching (.+)\. Signal (\S+) to green, please\.", lambda st, sg: f"A chegar {to('a', st)}. Sinal {sg} a verde, por favor."),
    (r"Ready to leave (.+) on track (\d+)\. Signal (\S+) to green, please\.",
     lambda st, n, sg: f"Pronto para partir {to('de', st)} na via {n}. Sinal {sg} a verde, por favor."),
    (r"Coming through (.+)\. Signal (\S+) to green, please\.", "A passar por {}. Sinal {} a verde, por favor."),
    (r"Approaching (.+)\. Please set points (\S+) to (.+) for me\.",
     lambda st, p, tr: f"A chegar {to('a', st)}. Põe a agulha {p} para a {track(tr)}, por favor."),
    (r"Points (\S+) are set against me on (.+)\. Please set them back\.",
     lambda p, tr: f"A agulha {p} está contra mim na {track(tr)}. Volta a pô-la como estava, por favor."),
    (r"I'm on (.+) at (.+)\. Please set points (\S+) so I can get out\.",
     lambda tr, st, p: f"Estou na {track(tr)} {to('em', st)}. Põe a agulha {p} para eu poder sair, por favor."),
    (r"Ready to leave (.+) from (.+)\. Signal (\S+) to green, please\.",
     lambda st, tr, s: f"Pronto para partir {to('de', st)} da {track(tr)}. Sinal {s} a verde, por favor."),
    (r"Coming to (.+) on (.+)\. Signal (\S+) to green, please\.",
     lambda st, tr, s: f"A chegar {to('a', st)} pela {track(tr)}. Sinal {s} a verde, por favor."),
    # What a signal, points or train is, under the mouse.
    (r"(\S+ \d+) to ([^·]+)", lambda tr, p: f"{tr} {to('para', p)}"),
    (r"next stop ([^·]+) (\S+)", "próxima paragem: {} {}"),
    (r"track (\d+)", "via {}"),
    (r"on ([^·]+)", lambda tr: f"na {track(tr)}"),
    (r"Signal (\S+)", "Sinal {}"),
    (r"([^·]+) entry", lambda st: f"entrada {to('de', st)}"),
    (r"([^·]+) track (\d+) exit", lambda st, n: f"saída da via {n} {to('de', st)}"),
    (r"([^·]+), (the [^·]+|platform \d+|track \d+)", lambda st, tr: f"{st}, {track(tr)}"),
    (r"Points (\S+)", "Agulha {}"),
    (r"set to track (\d+)", "para a via {}"),
    (r"set to ([^·]+)", lambda tr: f"para a {track(tr)}"),
    # Anything else made of parts, last: "R · Regional", "Regional · Freight".
    (r"(.+?) · (.+)", lambda a, b: f"{i18n.t(a, False)} · {i18n.t(b, False)}"),
]
