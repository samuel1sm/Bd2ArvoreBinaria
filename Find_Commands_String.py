import re
import numpy as np
import networkx as nx
import random
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
from Node import Node

# Setup --------------------------------------------------------

# query = "SELECT EMPLOYEE.LNAME FROM EMPLOYEE, WORKS_ON, PROJECT WHERE project.PNAME = Aquarius AND project.PNUMBER = WORKS_ON.PNO " \
#         "AND EMPLOYEE.ESSN = WORKS_ON.SSN AND WORKS_ON.BDATE > 1957-12-31"
# query = "select pessoa.nome,pessoa.idade from pessoa where pessoa.sexo = m and pessoa.idade > 30"
# query = "select cliente.nome, cliente.idade, cartao.tipo_c from " \
#         "batata, (select * from cliente join cartao on cartao.usuario = cliente.usuario)"



# query = "select * from cliente join cartao on cartao.usuario = cliente.usuario"

# query = "select pessoa.nome, pessoa.idade from pessoa join funcionario on pessoa.nome = funcionario.nome" \
#         " where pessoa.sexo = m and pessoa.idade > 30 order by pessoa.idade"



comandos = ["select ", " from ", " where ", " join ", " on ", " order by "]
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
                # for char in i:
                #     if char == '‘' or char == '’':
                #         in_quotes = not in_quotes
                #
                #     if char != ' ' or in_quotes:
                #         new_string += char
                # TODO / Os espaços foram removidos nesse for, mas não para o que está dentro de aspasg
                infos = i.split(operador)
                infos.append(operador)
                conditions.append(tuple(infos))

    return op_logicos_positions, conditions


def generate_tree(key, sub_queries, relations):
    # Guardando todos os nós
    all_nodes = []

    # Pegando todas as tabelas do from e separando a primeira das outras
    from_tables = sub_queries[key][" from "].replace(" from ", "").replace(" ", "").split(",")

    first = from_tables[0]
    from_tables.remove(first)
    other_tables = from_tables

    # Criando o primeiro nó e adicionando a tabela dele na lista de tabelas checadas
    if "!" in first:
        last_node_checked = generate_tree(first, sub_queries, relations)
        last_node_checked.data = f"({last_node_checked.data} ({first}))"

    else:
        last_node_checked = Node(first)

    all_nodes.append(last_node_checked)
    checked_tables = [first]

    # Pegando todos os wheres e joins e os colocando em vetores
    wheres = []
    joins = []

    for comparison in relations[key]["comparisons"]:
        if "where" in str(list(comparison)[-1]).strip():
            wheres.append(list(comparison))
        elif "join" in str(list(comparison)[-1]).strip():
            joins.append(list(comparison))

    # Adicionando as outras tabelas do from como joins
    for new_join in other_tables:
        joins.append((first, None, None, new_join, None, "join"))

    # print(wheres)
    # print(joins)

    # Primeira checagem de wheres
    wheres_to_remove = []
    for where in wheres:
        if can_use_where(where, checked_tables):
            wheres_to_remove.append(where)
            newnode = Node(where)  # TODO BUILD OPERATION STRING
            all_nodes.append(newnode)
            newnode.add_child(last_node_checked)
            last_node_checked = newnode

    for where in wheres_to_remove:
        wheres.remove(where)

    # Checagem de join e criação de nós filhas daquele join
    for join in joins:
        # Encontrando a tabela "diferente" que está no join
        join_table_name = join[3] if (join[0] in first) else join[0]
        checked_tables.append(join_table_name)

        if "!" in join_table_name:
            last_child_checked = generate_tree(join_table_name, sub_queries, relations)
            last_child_checked.data = f"({last_child_checked.data} ({join_table_name}))"
        else:
            last_child_checked = Node(join_table_name)

        all_nodes.append(last_child_checked)

        # Descendo a partir do join
        wheres_to_remove = []
        for where in wheres:
            if can_use_where(where, join_table_name):
                wheres_to_remove.append(where)
                newnode = Node(where)  # TODO BUILD OPERATION STRING
                all_nodes.append(newnode)
                newnode.add_child(last_child_checked)
                last_child_checked = newnode

        for where in wheres_to_remove:
            wheres.remove(where)

        # Juntando o node anterior com a child
        if type(last_node_checked.data) == tuple or type(last_node_checked.data) == list:
            join_child_1 = last_node_checked.data[0]
        else:
            join_child_1 = str(last_node_checked.data).strip()

        if type(last_child_checked.data) == tuple or type(last_child_checked.data) == list:
            join_child_2 = last_child_checked.data[0]
        else:
            join_child_2 = str(last_child_checked.data).strip()

        newnode = Node((join_child_1, None, None, join_child_2, None, "join"))
        all_nodes.append(newnode)
        newnode.add_children(last_node_checked, last_child_checked)
        last_node_checked = newnode

        # Após o join, vendo se tem wheres restantes possíveis antes do próximo join
        wheres_to_remove = []
        for where in wheres:
            if can_use_where(where, checked_tables):
                wheres_to_remove.append(where)
                newnode = Node(where)  # TODO BUILD OPERATION STRING
                all_nodes.append(newnode)
                newnode.add_child(last_node_checked)
                last_node_checked = newnode

        for where in wheres_to_remove:
            wheres.remove(where)

    # Adicionando os order by, se existirem
    if " order by " in sub_queries[key]:
        order_bys = sub_queries[key][" order by "].replace(" order by ", "").split()
        order_bys = [i for i in order_bys if i]

        for order in order_bys:
            newnode = Node("order by " + order)
            all_nodes.append(newnode)
            newnode.add_child(last_node_checked)
            last_node_checked = newnode

    # Adicionando o select
    newnode = Node(str(sub_queries[key]["select "]))
    all_nodes.append(newnode)
    newnode.add_child(last_node_checked)
    last_node_checked = newnode

    return last_node_checked


def create_tree_dictionary(root):
    tree = {}
    level = 0
    id = 1

    thislevel = [(root, " [#" + str(1) + "/")]

    while thislevel:
        nextlevel = list()
        level_data_array = []

        for n in thislevel:
            if type(n[0].data) == tuple or type(n[0].data) == list:
                n[0].data = build_operation_string(n[0].data)

            node_string_build = n[0].data + n[1]

            if n[0].left_node:
                id += 1
                nextlevel.append((n[0].left_node, " [#" + str(id) + "/"))
                node_string_build += str(id)
            if n[0].right_node:
                id += 1
                nextlevel.append((n[0].right_node, " [#" + str(id) + "/"))
                node_string_build += "/" + str(id)

            node_string_build += "]"
            level_data_array.append(node_string_build)


        tree[str(level)] = level_data_array

        # print()
        thislevel = nextlevel
        level += 1

    print(tree)
    return tree


def can_use_where(where: list, tables: []):
    if where[0] in tables:
        if (not where[4]) or (where[4] in tables):
            return True
        else:
            return False
    else:
        return False


def build_operation_string(oper: list):
    operation_string = ""

    if oper[5] == "where":
        operation_string += "where " + oper[0] + "." + oper[1] + " " + oper[2] + " " + oper[3]

        if oper[4]:
            operation_string += "." + oper[4]

    elif oper[5] == "join":
        operation_string += oper[0] + " join " + oper[3]

        if oper[1] and oper[2] and oper[4]:
            operation_string += " on " + oper[0] + "." + oper[1] + " " + oper[2] + oper[3] + "." + oper[4]

    return operation_string


# Codigo -------------------------------------------------------

def verify_query(query):
    query = query.lower()
    select_positions = [m.start() for m in re.finditer("select", query)]
    select_positions.reverse()

    sub_queries = {}

    # print(query, end="\n\n")

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
                # index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
                next_data = sub_positions[i + 1]
                result[current_data[0]] = sub_query[current_data[1]: next_data[1]]
            else:
                # index_start = current_data[1] if sub_query[current_data[1]] != ' ' else (current_data[1] + 1)
                result[current_data[0]] = sub_query[current_data[1]:]

        # Dicionário de dicionários. Result é tanto a query toda quanto ela "dividida"
        sub_queries[key] = result

    # Printando cada select e subselect, junto com sua chave
    # for key in sub_queries:
    #     print(key)
    #     i = sub_queries[key]
    #     for key2 in sub_queries[key]:
    #         print(f"{key2}: {i[key2]}")
    #
    # print()

    operators_dict = {}
    for key in sub_queries:
        operators_dict[key] = {}
        if " where " in sub_queries[key]:
            a = sub_queries[key][" where "].replace("where ", "")
            operators_dict[key][" where "] = split_operators(op_comparacao, op_logicos, a)

        if " on " in sub_queries[key]:
            a = sub_queries[key][" on "].replace(" on ", "")
            operators_dict[key][" on "] = split_operators(op_comparacao, op_logicos, a)

    # print(sub_queries, end="\n\n")
    # print(operators_dict, end="\n\n")

    relations = {}

    # Procurando todas as tabelas distintas e as colunas de cada tabela e as colocando no dicionário sub_queries
    for query in sub_queries:
        relations[query] = {}
        relations[query]["tabelas"] = []
        relations[query]["columns_info"] = {}
        relations[query]["select_infos"] = {}
        relations[query]["comparisons"] = []

        if "select " in sub_queries[query]:
            aux_array = sub_queries[query]["select "].replace("select ", '').replace(" ", '').split(",")

            for tab in aux_array:
                if tab != "*":
                    tabela_info, column = tab.split(".")
                    if tabela_info not in relations[query]["select_infos"]:
                        relations[query]["select_infos"][tabela_info] = []
                    relations[query]["select_infos"][tabela_info].append(column)
                else:
                    relations[query]["select_infos"]["all"] = [tab]

        if " from " in sub_queries[query]:
            aux_array = sub_queries[query][" from "].replace(" from ", '').replace(" ", '').split(",")

            for tab in aux_array:
                if tab not in relations[query]["tabelas"]:
                    relations[query]["tabelas"].append(tab)

        if " join " in sub_queries[query]:
            aux_array = sub_queries[query][" join "].replace(" join ", '').replace(" ", '').split(",")

            for tab in aux_array:
                if tab not in relations[query]["tabelas"]:
                    relations[query]["tabelas"].append(tab)

            a = operators_dict[query][" on "][1]

            for operation in a:
                if "." in operation[0]:
                    tabela_info_l, column_l = operation[0].split(".")
                else:
                    column_l = None
                    tabela_info_l = operation[0]

                if "." in operation[1]:
                    tabela_info_r, column_r = operation[1].split(".")
                else:
                    column_r = None
                    tabela_info_r = operation[1]

                if column_r and tabela_info_r not in relations[query]["columns_info"]:
                    relations[query]["columns_info"][tabela_info_r] = []

                if column_r and tabela_info_l not in relations[query]["columns_info"]:
                    relations[query]["columns_info"][tabela_info_l] = []

                relations[query]["comparisons"].append(
                    (tabela_info_l, column_l, operation[2], tabela_info_r, column_r, "join"))
                relations[query]["columns_info"][tabela_info_r].append(column_r)
                if column_r:
                    relations[query]["columns_info"][tabela_info_l].append(column_l)

            # sub_queries[query]["on"].replace(" on ", '').replace(" ", '').split(",")

        if " where " in sub_queries[query]:
            a = operators_dict[query][" where "][1]
            for operation in a:
                if "." in operation[0]:
                    tabela_info_l, column_l = operation[0].split(".")
                else:
                    column_l = None
                    tabela_info_l = operation[0]

                if "." in operation[1]:
                    tabela_info_r, column_r = operation[1].split(".")
                else:
                    column_r = None
                    tabela_info_r = operation[1]

                tabela_info_l = tabela_info_l.strip()
                tabela_info_r = tabela_info_r.strip()

                if column_r and tabela_info_r not in relations[query]["columns_info"]:
                    relations[query]["columns_info"][tabela_info_r] = []

                if column_l and tabela_info_l not in relations[query]["columns_info"]:
                    relations[query]["columns_info"][tabela_info_l] = []

                relations[query]["comparisons"].append(
                    (tabela_info_l, column_l, operation[2], tabela_info_r, column_r, "where"))
                relations[query]["columns_info"][tabela_info_l].append(column_l)

                if column_r:
                    relations[query]["columns_info"][tabela_info_r].append(column_r)

    a = generate_tree(list(sub_queries.keys())[-1], sub_queries, relations)
    return create_tree_dictionary(a)
# print(relations)
# print("!!!!!!!!!!!!")
# print(sub_queries)
#
# a = list(sub_queries.keys())
# a.sort(reverse=True)
#
# print(a)
#
# infos = relations[a[0]]
# tabelas = infos["tabelas"]
# columns_info = infos["columns_info"]
# select_infos = infos["select_infos"]
#
# print(tabelas)
# print(columns_info)
# print(select_infos)
#
# print()

# for i, col in enumerate(tabelas):
#     if i == 0:
#         tree.left_node = generate_tree(col, relations) if "!" in col else Node(col)
#     else:
#         tree.right_node = generate_tree(col, relations) if "!" in col else Node(col)
#
# print(infos)

# for t in tabelas:
#     Node()


# Pegando tabelas e colunas a partir do where


def hierarchy_pos(G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  # allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None):

        if pos is None:
            pos = {root: (xcenter, vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)
        if len(children) != 0:
            dx = width / len(children)
            nextx = xcenter - width / 2 - dx / 2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G, child, width=dx, vert_gap=vert_gap,
                                     vert_loc=vert_loc - vert_gap, xcenter=nextx,
                                     pos=pos, parent=root)
        return pos

    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)



if __name__ == '__main__':
    G = nx.DiGraph()
    query = "select cliente.nome,cliente.idade,cartao.tipo_c from " \
            "(select * from cliente join cartao on cartao.usuario = cliente.usuario)," \
            "(select batata.azedagem,cliente.nome,cliente.usuario from batata join cliente on batata.usuario = cliente.usuario)"
    x = verify_query(query)
    labels = {}
    for level in x.values():
        for node in level:
            ident = node.split('#')[1].split("/")[0]
            label = node.split('[')[0]
            if len(label) > 30:
                list_label = label.split(' ')
                list_label.insert(int(len(label.split(' '))/2), '\n')
                label = ' '.join(list_label)
            labels[ident] = label
            nodes = node.split('#')[1].split("]")[0].split('/')
            x = []
            for y in nodes:
                if y != '':
                    x.append(y)
            nodes = x
            if ident not in labels.keys():
                G.add_node(ident)
            if len(nodes) > 1:
                if nodes[1] not in labels.keys():
                    G.add_node(nodes[1])
                G.add_edge(ident, nodes[1])
            if len(nodes) > 2:
                if nodes[2] not in labels.keys():
                    G.add_node(nodes[2])
                G.add_edge(ident, nodes[2])
    G = nx.relabel_nodes(G, labels)

    pos = hierarchy_pos(G, labels['1'])
    nx.draw(G, pos, with_labels=True,node_size=8500, font_size=20,node_color='w')
    plt.savefig('plot.png')
    plt.show()

    pass
    print()