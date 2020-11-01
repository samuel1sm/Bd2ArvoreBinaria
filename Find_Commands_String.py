import re
import numpy as np

# Setup --------------------------------------------------------

query = "SELECT LNAME FROM EMPLOYEE, WORKS_ON, PROJECT WHERE project.PNAME = ‘Aquarius’ OR project.PNUMBER = PNO " \
        "AND EMPLOYEE.ESSN = SSN AND WORKS_ON.BDATE > ‘1957-12-31’"
# query = "select pessoa.nome,pessoa.idade from pessoa where pessa.idade = 20"
# query = "select nome,idade,tipo_c from (select * from cliente join cartao on cartao.usuario = cliente.usuario),batata"

query = query.lower()

comandos = ["select ", " from ", " where ", " join ", " on ", "order by"]
op_comparacao = ["=", ">", "<", "<=", ">=", "<>"]
op_logicos = [" and ", " or ", " in ", " not in ", " like "]


# Metodos ------------------------------------------------------

def split_operators(op_comp, op_logic, query: str):

    # Preenchendo vetor de operadores logicos (and, or, in, etc.) e os reorganizando
    op_logicos_positions = []

    for operador in op_logic:
        # TODO / Os espaços foram removidos com o .strip() em operator
        op_logicos_positions.extend([(m.start(), operador.strip()) for m in re.finditer(operador, query)])
        query = query.replace(operador, "!_!")

    op_logicos_positions.sort(key=lambda tup: tup[0])
    comparacoes = query.split("!_!")

    # Preenchendo vetor de tuplas de condicoes (=, <, >, etc.)
    conditions = []
    for operador in op_comp:
        for i in comparacoes:
            if operador in i:
                new_string = ''
                in_quotes = False

                for char in i:
                    if char == '‘' or char == '’':
                        in_quotes = not in_quotes

                    if char != ' ' or in_quotes:
                        new_string += char
                    # TODO / Os espaços foram removidos nesse for, mas não para o que está dentro de aspas

                i = new_string
                infos = i.split(operador)
                infos.append(operador)
                conditions.append(tuple(infos))

    print(op_logicos_positions)
    print(conditions)

    return op_logicos_positions, conditions


# Codigo -------------------------------------------------------

select_positions = [m.start() for m in re.finditer("select", query)]
select_positions.reverse()

sub_queries = {}

print(query)

# Para cada select e subselect
for i, position in enumerate(select_positions):

    # Criando uma chave para cada select e trocando esse select pela chave na string
    key = f"!{i}!"
    sub_query = query[position:].split(")")[0]
    query = query.replace(f"({sub_query})", key)

    # Procurando todas as operações (select, etc.), colocando elas em sub_positions e organizando elas conforme a string
    sub_positions = []

    for comando in comandos:
        sub_position = sub_query.find(comando)
        if sub_position == -1:
            continue
        sub_positions.append((comando, sub_position))

    sub_positions.sort(key=lambda tup: tup[1])

    # Dividindo o select/subselect em partes
    result = {}

    result["query"] = sub_query
    for i, current_data in enumerate(sub_positions):
        if i != len(sub_positions) - 1:
            # TODO / Os espaços são removidos com o .strip() em current_data[0]. Ver com samuel o index_start abaixo.
            #index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
            next_data = sub_positions[i + 1]
            result[current_data[0].strip()] = sub_query[current_data[1]: next_data[1]]
        else:
            #index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
            result[current_data[0].strip()] = sub_query[current_data[1]:]

    # Dicionário de dicionários. Result é tanto a query toda quanto ela "dividida"
    sub_queries[key] = result

print()

# Printando cada select e subselect, junto com sua chave
for key in sub_queries:
    print(key)
    i = sub_queries[key]
    for key2 in sub_queries[key]:
        print(f"{key2}: {i[key2]}")

print()

# Esqueci o que isso faz, perguntar ao Samuel. Mas nessa query não faz nada pq não tem where
operators_dict = {}
for key in sub_queries:
    if " where " in sub_queries[key]:
        a = sub_queries[key][" where "].replace("where ", "")
        operators_dict[key] = split_operators(op_comparacao, op_logicos, a)

print(operators_dict, end="\n\n")
print(sub_queries, end="\n\n")

# Procurando todas as tabelas distintas e as colunas de cada tabela e as colocando no dicionário sub_queries
for query in sub_queries:
    sub_queries[query]["tabelas"] = ""

    # Pegando tabelas a partir do from
    if "from" in sub_queries[query]:
        aux_array = sub_queries[query]["from"].split(' ')
        aux_array = [i for i in aux_array if i]

        for tabela in aux_array[1:]:
            if tabela not in sub_queries[query]["tabelas"]:
                tabela.replace(',', '')

                if sub_queries[query]["tabelas"] != "":
                    sub_queries[query]["tabelas"] += ","

                sub_queries[query]["tabelas"] += tabela

    # Pegando uma tabela a partir do join
    if "join" in sub_queries[query]:
        aux_array = sub_queries[query]["join"].split(' ')
        aux_array = [i for i in aux_array if i]
        # TODO / Checar se tudo daqui pro próximo TODO está certo
        tabela = aux_array[1]

        if tabela not in sub_queries[query]["tabelas"]:
            tabela.replace(',', '')

            if sub_queries[query]["tabelas"] != "":
                sub_queries[query]["tabelas"] += ","

            sub_queries[query]["tabelas"] += tabela
        # TODO --------------------------------------------------

    # Pegando tabelas e colunas a partir do where
    if "where" in sub_queries[query]:
        aux_array = sub_queries[query]["where"].split('.')

        for i, element in enumerate(aux_array):
            # Tabelas
            if i != len(aux_array) - 1 and element.split(' ')[-1] not in sub_queries[query]["tabelas"]:
                sub_queries[query]["tabelas"] += "," + element.split(' ')[-1]

            # Colunas
            if i != 0:
                aux_tabela = aux_array[i-1].split(' ')[-1]
                aux_coluna = element.split(' ')[0]

                # Se a tabela não existir como item do sub_queries, ela é adicionada
                if ("t/" + aux_tabela) not in sub_queries[query]:
                    sub_queries[query]["t/" + aux_tabela] = ""

                # Adicionando a coluna da tabela associada no sub_queries
                if aux_coluna not in sub_queries[query]["t/" + aux_tabela]:
                    if sub_queries[query]["t/" + aux_tabela] != "":
                        sub_queries[query]["t/" + aux_tabela] += ","

                    sub_queries[query]["t/" + aux_tabela] += aux_coluna

    # TODO select?

print(sub_queries)

# if "select" in sub_queries[query]:
#     print(sub_queries[query]["select"])

# --------------------------------------------------------------

# print(sub_querrys)
# print(querry)

# for comando in comandos:
#     print("----------------")
#     print(comando)
#     result = [m.start() for m in re.finditer(comando, sql)]
#
#     if len(result) > 0:
#         positions.update({comando: result})
#     print(result)

# PNAME = ‘Aquarius’ AND project.PNUMBER = PNO AND ESSN = SSN AND BDATE > ‘1957-12-31’
# query = " PNAME = ‘Aquarius’ AND project.PNUMBER = PNO !_! ESSN = SSN !_! BDATE > ‘1957-12-31’"
# query = " PNAME = ‘Aquarius’ !_! project.PNUMBER = PNO !_! ESSN = SSN !_! BDATE > ‘1957-12-31’"
