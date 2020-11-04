import re
import numpy as np

# Setup --------------------------------------------------------

# query = "SELECT LNAME FROM EMPLOYEE, WORKS_ON, PROJECT WHERE project.PNAME = Aquarius OR project.PNUMBER = PNO " \
#         "AND EMPLOYEE.ESSN = SSN AND WORKS_ON.BDATE > 1957-12-31"
query = "select pessoa.nome,pessoa.idade from pessoa where pessoa.sexo = m"
# query = "select cliente.nome,cliente.idade,cartao.tipo_c from (select * from cliente join cartao on cartao.usuario = cliente.usuario),batata"

query = query.lower()

comandos = ["select ", " from ", " where ", " join ", " on ", "order by"]
op_comparacao = ["=", ">", "<", "<=", ">=", "<>"]
op_logicos = [" and ", " or ", " in ", " not in ", " like "]


# Metodos ------------------------------------------------------

def split_operators(op_comp, op_logic, query: str):
    # Preenchendo vetor de operadores logicos (and, or, in, etc.) e os reorganizando
    op_logicos_positions = []

    for operador in op_logic:
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
            # index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
            next_data = sub_positions[i + 1]
            result[current_data[0].strip()] = sub_query[current_data[1]: next_data[1]]
        else:
            # index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
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

# Esqueci o que isso faz, perguntar ao Samuel. Mas nessa query não faz nada pq não tem where
operators_dict = {}
for key in sub_queries:
    operators_dict[key] = {}
    if "where" in sub_queries[key]:
        a = sub_queries[key]["where"].replace("where ", "")
        operators_dict[key]["where"] = split_operators(op_comparacao, op_logicos, a)

    if "on" in sub_queries[key]:
        a = sub_queries[key]["on"].replace(" on ", "")
        operators_dict[key]["on"] = split_operators(op_comparacao, op_logicos, a)

print(sub_queries, end="\n\n")
print(operators_dict, end="\n\n")

relations = {}
# Procurando todas as tabelas distintas e as colunas de cada tabela e as colocando no dicionário sub_queries
for query in sub_queries:
    relations[query] = {}
    relations[query]["tabelas"] = []
    relations[query]["columns_info"] = {}
    relations[query]["select_infos"] = {}

    if "select" in sub_queries[query]:
        aux_array = sub_queries[query]["select"].replace("select ", '').replace(" ", '').split(",")

        for tab in aux_array:
            if tab != "*":
                tabela_info, column = tab.split(".")
                if tabela_info not in relations[query]["select_infos"]:
                    relations[query]["select_infos"][tabela_info] = []
                relations[query]["select_infos"][tabela_info].append(column)
            else:
                relations[query]["select_infos"]["all"] = [tab]

    if "from" in sub_queries[query]:
        aux_array = sub_queries[query]["from"].replace(" from ", '').replace(" ", '').split(",")

        for tab in aux_array:
            if tab not in relations[query]["tabelas"]:
                relations[query]["tabelas"].append(tab)

    if "join" in sub_queries[query]:
        aux_array = sub_queries[query]["join"].replace(" join ", '').replace(" ", '').split(",")

        for tab in aux_array:
            if tab not in relations[query]["tabelas"]:
                relations[query]["tabelas"].append(tab)

        a = operators_dict[query]["on"][1]

        for tabela_info, value, _ in a:
            tabela_info, column = tabela_info.split(".")
            if tabela_info not in relations[query]["columns_info"]:
                relations[query]["columns_info"][tabela_info] = []

            relations[query]["columns_info"][tabela_info].append(column)

        # sub_queries[query]["on"].replace(" on ", '').replace(" ", '').split(",")

    if "where" in sub_queries[query]:

        a = operators_dict[query]["where"][1]
        for tabela_info, value, _ in a:
            tabela_info, column = tabela_info.split(".")
            if tabela_info not in relations[query]["columns_info"]:
                relations[query]["columns_info"][tabela_info] = []

            relations[query]["columns_info"][tabela_info].append(column)

print(relations)
# Pegando tabelas e colunas a partir do where
